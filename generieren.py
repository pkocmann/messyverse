#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""generieren.py -- seed-fester Generator des messyverse-Uebungsuniversums.

Baut das komplette Welt-Universum reproduzierbar aus den gepinnten API-Fixtures
(api-fixtures/, Wahrheitsquelle fuer die Bibliografie). Dazu das Berichtswesen
verwaltung/statistik/ (Mehrjahresdaten fuer Statistik-Kurse, eigener Zufallsstrom
STAT_SEED, damit der uebrige Bestand byte-gleich bleibt; Kanon: WELT.md). Dieser Generator geht
NIE ins Netz -- so bleibt das Reproduzieren-Gate (E6) stabil: zwei Laeufe
hintereinander erzeugen byte-identische Dateien.

Drift-Schutz (E6):
  - feste Seed-Zahl (SEED); jede Zufallsentscheidung laeuft ueber RNG.
  - Marker "GENERIERT -- nicht editieren" in jeder erzeugten Datei/Kopfzeile.
  - deterministische Timestamps fuer PDF (reportlab invariant) und xlsx
    (Zip-Member-Zeiten normalisiert + feste docProps).
  - Reproduzieren-Gate: `python generieren.py && git diff --exit-code` muss sauber sein.

Regeneration bei Schema-Aenderung: zuerst WELT.md aktualisieren, dann diesen
Generator, dann neu laufen lassen und das Reproduzieren-Gate pruefen.

Lauf:  aus messyverse/ mit der gemeinsamen venv:  .venv/bin/python generieren.py
"""

import csv
import hashlib
import io
import json
import math
import pathlib
import random
import shutil
import zipfile
from datetime import datetime

import reportlab.rl_config
reportlab.rl_config.invariant = 1  # feste PDF-CreationDate + Doc-ID -> reproduzierbare Bytes
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

import openpyxl

# ------------------------------------------------------------------ Konstanten
SEED = 20250101
DATUM_FIX = datetime(2025, 12, 31, 0, 0, 0)  # deterministischer Datei-Timestamp
ZIP_FIX = (1980, 1, 1, 0, 0, 0)              # feste Zip-Member-Zeit (xlsx)
MARKER = "GENERIERT -- nicht editieren (Quelle: generieren.py). Aenderungen gehen beim naechsten Lauf verloren."
LIEFERANT = "Quellmann Fachbuch GmbH"
ORG = "Institut fuer Verwaltungs- und Regionalkunde -- Bibliothek und Archiv"

ROOT = pathlib.Path(__file__).resolve().parent
OL_DIR = ROOT / "api-fixtures" / "openlibrary"

# ------------------------------------------------------------------ Katalog (13 Titel, kuratiert + live verifiziert 2026-06-23)
# kurztitel/autor = saubere Anzeige; die echten (teils unsauberen) Lookup-Daten liefert die Fixture.
# kette: 'voll' (Rechnung+Haushalt+Vermerk) | 'kein_beleg' | 'rechnung_ohne_haushalt' | 'rechnung_ohne_betrag'
KATALOG = [
    {"isbn": "9783150012413", "kurztitel": "Selbstbetrachtungen",        "autor": "Marcus Aurelius",      "jahr": 2005, "preis": 8.80,  "kat": "Philosophie & Ethik"},
    {"isbn": "9781503901599", "kurztitel": "Rechte der Frau",            "autor": "Mary Wollstonecraft",  "jahr": 2018, "preis": 14.50, "kat": "Gesellschaft & Soziales"},
    {"isbn": "9781974384594", "kurztitel": "Frederick Douglass",         "autor": "Frederick Douglass",   "jahr": 2017, "preis": 12.00, "kat": "Geschichte & Politik"},
    {"isbn": "9783518111383", "kurztitel": "Okonkwo",                     "autor": "Chinua Achebe",        "jahr": 1998, "preis": 16.00, "kat": "Literatur & Sprache"},
    {"isbn": "9783499130656", "kurztitel": "Menschenkind",               "autor": "Toni Morrison",        "jahr": 1995, "preis": 13.00, "kat": "Literatur & Sprache"},
    {"isbn": "9783596162505", "kurztitel": "Hundert Jahre Einsamkeit",   "autor": "Gabriel Garcia Marquez","jahr": 2014, "preis": 15.00, "kat": "Literatur & Sprache"},
    {"isbn": "9781979725033", "kurztitel": "Stolz und Vorurteil",        "autor": "Jane Austen",          "jahr": 2017, "preis": 9.90,  "kat": "Literatur & Sprache"},
    {"isbn": "9798844408786", "kurztitel": "Crime and Punishment",       "autor": "F. Dostojewski",       "jahr": 2022, "preis": 11.50, "kat": "Literatur & Sprache"},
    {"isbn": "9783458333593", "kurztitel": "Prinz Genji",               "autor": "Murasaki Shikibu",     "jahr": 1995, "preis": 48.00, "kat": "Literatur & Sprache"},
    {"isbn": "9783293200654", "kurztitel": "Zwischen den Palaesten",     "autor": "Nagib Machfus",        "jahr": 1996, "preis": 22.00, "kat": "Literatur & Sprache"},
    {"isbn": "9783763231690", "kurztitel": "Das Geisterhaus",            "autor": "Isabel Allende",       "jahr": 1984, "preis": 24.00, "kat": "Literatur & Sprache"},
    {"isbn": "9781533358905", "kurztitel": "Gitanjali",                  "autor": "Rabindranath Tagore",  "jahr": 2016, "preis": 10.00, "kat": "Religion & Weltanschauung"},
    {"isbn": "9783499166211", "kurztitel": "Das andere Geschlecht",      "autor": "Simone de Beauvoir",   "jahr": 1991, "preis": 19.90, "kat": "Gesellschaft & Soziales"},
]

DOIS = [
    "10.1038/sdata.2016.18", "10.7717/peerj.4375", "10.1073/pnas.0507655102",
    "10.1108/eb026583", "10.1002/asi.20416", "10.1515/pdtc-2024-2001",
]

# ------------------------------------------------------------------ Rechnungen (Querverweis-Kette E2)
# datum_fmt mischt bewusst Formate (TT.MM.JJJJ / ISO / deutsch lang) -> Vereinheitlichungs-Uebung.
# 10 Buecher in vollstaendigen Ketten, 3 bewusst unvollstaendig.
# Drei bewusste Unvollstaendigkeiten (Lernanlass "was fehlt?"):
#   - #12 Tagore (9781533358905) steht im Katalog, aber in KEINER Rechnung   -> Katalogeintrag ohne Beleg
#   - RE-2025-0003 fuehrt de Beauvoir OHNE Einzelpreis                         -> Rechnung ohne Betragszeile
#   - RE-2025-0008 (Dostojewski) hat KEINE Haushaltszeile und KEINEN Vermerk   -> Rechnung ohne Haushaltsbuchung
# Die uebrigen 9 Buecher laufen durch die vollstaendige Kette (Rechnung -> Katalog -> Haushalt -> Vermerk).
RECHNUNGEN = [
    {"nr": "RE-2025-0001", "datum": "2025-03-15", "datum_fmt": "15.03.2025",      "isbns": ["9783150012413", "9783458333593"], "haushalt": True,  "vermerk": True},
    {"nr": "RE-2025-0002", "datum": "2025-04-08", "datum_fmt": "2025-04-08",      "isbns": ["9783518111383", "9783499130656", "9783763231690"], "haushalt": True, "vermerk": True},
    {"nr": "RE-2025-0003", "datum": "2025-05-03", "datum_fmt": "3. Mai 2025",     "isbns": ["9781503901599", "9783499166211"], "haushalt": True,  "vermerk": True, "ohne_betrag": ["9783499166211"]},
    {"nr": "RE-2025-0004", "datum": "2025-06-20", "datum_fmt": "20.06.2025",      "isbns": ["9783596162505"],                   "haushalt": True,  "vermerk": True},
    {"nr": "RE-2025-0005", "datum": "2025-09-12", "datum_fmt": "2025-09-12",      "isbns": ["9781974384594", "9781979725033", "9783293200654"], "haushalt": True, "vermerk": True},
    {"nr": "RE-2025-0008", "datum": "2025-11-05", "datum_fmt": "5. November 2025","isbns": ["9798844408786"],                   "haushalt": False, "vermerk": False},
]

SCHLAGWORTE = [
    ("Philosophie & Ethik",        "Denkschulen, Moral, Lebensfuehrung"),
    ("Geschichte & Politik",       "Historische Ereignisse, Staat, Gesellungsformen"),
    ("Literatur & Sprache",        "Romane, Lyrik, Erzaehlungen, Sprachwissenschaft"),
    ("Gesellschaft & Soziales",    "Soziale Fragen, Geschlecht, Teilhabe, Recht"),
    ("Naturwissenschaft & Technik","Natur, Mathematik, Ingenieurwesen, Informatik"),
    ("Religion & Weltanschauung",  "Glaube, Spiritualitaet, Weltdeutung"),
    ("Kunst & Kultur",             "Bildende Kunst, Musik, Theater, Kulturgeschichte"),
]
PFLICHT_FACETTEN = ["Literatur & Sprache", "Gesellschaft & Soziales", "Philosophie & Ethik"]

# magazin/: Scan-Zoo mit gewachsenen Namen. datum=None -> nicht datierbar (Sammelordner "undatiert").
MAGAZIN = [
    {"name": "Scan_2025_03_final_FINAL_v2.pdf",            "datum": "2025-03-15", "text": "Lieferschein Maerz 2025"},
    {"name": "dokument (3).pdf",                            "datum": "2025-04-08", "text": "Begleitzettel zur Lieferung"},
    {"name": "Rechnung_Quellmann_2025-04-08.pdf",          "datum": "2025-04-08", "text": "Zweitscan einer Rechnung"},
    {"name": "Bestellung 2025_09.pdf",                     "datum": "2025-09-12", "text": "Bestellnotiz September"},
    {"name": "protokoll 2. Maerz 2025.pdf",                "datum": "2025-03-02", "text": "Sitzungsprotokoll"},
    {"name": "Behoerden-Uebersicht_Aussenstelle.pdf",      "datum": "2025-06-20", "text": "Uebersicht Aussenstelle (Umlaute/Sonderzeichen im Namen)"},
    {"name": "Vermerk_Erwerbung_Q2.pdf",                   "datum": "2025-06-30", "text": "Quartalsvermerk Erwerbung"},
    {"name": "scan0001.pdf",                               "datum": "2025-05-03", "text": "Allgemeiner Scan"},
    {"name": "Kopie von Lieferschein.pdf",                 "datum": "2025-10-01", "text": "Kopie eines Lieferscheins"},
    {"name": "2025_11_05 Eingang.pdf",                     "datum": "2025-11-05", "text": "Eingangsstempel November"},
    {"name": "IMG_0421.pdf",                               "datum": None,         "text": "Foto eines Dokuments ohne Datumshinweis"},
    {"name": "Notiz zB Rueckgabe.pdf",                     "datum": "2025-07-14", "text": "Notiz, z.B. zur Rueckgabe (z.B. verfaelscht naive Satzzaehlung)"},
    {"name": "final final FINAL.pdf",                      "datum": "2025-08-19", "text": "Mehrfach final benannte Datei"},
    {"name": "DOC20250912.pdf",                            "datum": "2025-09-12", "text": "Geraete-Export"},
    {"name": "leer_scan.pdf",                              "datum": None,         "text": None},  # 0-Byte-Datei (leerer Eintrag)
    {"name": "uebersicht_2025.pdf",                        "datum": "2025-12-01", "text": "Jahresuebersicht"},
    # echter Umlaut im Dateinamen (PB4 E6): bewusste Ausnahme von der ASCII-Dateinamen-Regel,
    # damit der Umlaut-Pfad real getestet wird (Filesystem -> JSON-Golden -> faithful NB04).
    {"name": "Behörden-Rückgabe März.pdf",                 "datum": "2025-03-21", "text": "Rueckgabe-Vermerk der Aussenstelle (Umlaut nur im Dateinamen)"},
]


# ------------------------------------------------------------------ Helfer
def rng_pin(seed=SEED):
    return random.Random(seed)


def schreibe_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def lese_fixture(isbn):
    d = json.loads((OL_DIR / f"{isbn}.json").read_text(encoding="utf-8"))
    return d.get(f"ISBN:{isbn}", {})


def pdf_schreiben(path, zeilen):
    """Einfaches Text-PDF (reportlab invariant -> reproduzierbare Bytes)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    y = 270 * mm
    for text, size, font in zeilen:
        c.setFont(font, size)
        for line in text.split("\n"):
            c.drawString(20 * mm, y, line)
            y -= (size + 4)
        y -= 2
    c.showPage()
    c.save()


def normalize_zip(path):
    """xlsx ist ein Zip: Member-Zeiten auf ZIP_FIX setzen + core.xml dcterms:modified fixieren
    (openpyxl setzt 'modified' beim Speichern hart auf now()) -> byte-stabile Ausgabe."""
    import re
    fix_iso = DATUM_FIX.strftime("%Y-%m-%dT%H:%M:%SZ")
    buf = io.BytesIO(path.read_bytes())
    out = io.BytesIO()
    with zipfile.ZipFile(buf) as zin:
        names = sorted(zin.namelist())
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                data = zin.read(name)
                if name == "docProps/core.xml":
                    text = data.decode("utf-8")
                    text = re.sub(r"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)",
                                  rf"\g<1>{fix_iso}\g<2>", text)
                    data = text.encode("utf-8")
                zi = zipfile.ZipInfo(name, date_time=ZIP_FIX)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = 0o600 << 16
                zout.writestr(zi, data)
    path.write_bytes(out.getvalue())


def euro(x):
    return f"{x:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ Generierung
def gen_katalog():
    kdir = ROOT / "katalog"
    # isbns.txt / dois.txt: reine Wertlisten OHNE "#"-Header -- ein Kommentar-Header laesst naive
    # Parser auf der ersten Zeile abstuerzen (adversariale Verifikation 2026-06-23). Drift ist hier
    # durch das Reproduzieren-Gate gedeckt; der GENERIERT-Marker steckt in den uebrigen Artefakten.
    schreibe_text(kdir / "isbns.txt", "\n".join(b["isbn"] for b in KATALOG) + "\n")
    schreibe_text(kdir / "dois.txt", "\n".join(DOIS) + "\n")
    # titel.csv (kuratierte Anzeige-Metadaten)
    with (kdir / "titel.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["isbn", "kurztitel", "autor", "jahr", "preis_eur", "kategorie"])
        for b in KATALOG:
            w.writerow([b["isbn"], b["kurztitel"], b["autor"], b["jahr"], f'{b["preis"]:.2f}', b["kat"]])
    # schlagworte.csv (kontrolliertes Vokabular E8/E12)
    with (kdir / "schlagworte.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kategorie", "beschreibung"])
        for k, b in SCHLAGWORTE:
            w.writerow([k, b])


def gen_rechnungen():
    edir = ROOT / "erwerbung"
    kat = {b["isbn"]: b for b in KATALOG}
    for r in RECHNUNGEN:
        ohne = set(r.get("ohne_betrag", []))
        zeilen = [
            (ORG, 9, "Helvetica"),
            (f"Lieferant: {LIEFERANT}", 11, "Helvetica-Bold"),
            ("", 4, "Helvetica"),
            (f"RECHNUNG  {r['nr']}", 14, "Helvetica-Bold"),
            (f"Rechnungsdatum: {r['datum_fmt']}", 10, "Helvetica"),
            ("", 4, "Helvetica"),
            ("Pos  ISBN             Kurztitel                         Einzelpreis", 9, "Courier"),
        ]
        summe = 0.0
        for i, isbn in enumerate(r["isbns"], 1):
            b = kat[isbn]
            if isbn in ohne:
                preis_txt = "(Betrag fehlt)"
            else:
                preis_txt = euro(b["preis"])
                summe += b["preis"]
            zeilen.append((f"{i:<4} {isbn}  {b['kurztitel'][:30]:<32} {preis_txt}", 9, "Courier"))
        zeilen += [
            ("", 4, "Helvetica"),
            (f"Rechnungsbetrag: {euro(summe)}", 11, "Helvetica-Bold"),
            ("", 6, "Helvetica"),
            (f"# {MARKER}", 7, "Helvetica"),
        ]
        pdf_schreiben(edir / f"{r['nr']}.pdf", zeilen)


def gen_haushalt():
    vdir = ROOT / "verwaltung"
    kat = {b["isbn"]: b for b in KATALOG}
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Haushalt 2025"
    ws.append(["rechnungsnr", "datum", "lieferant", "betrag_eur", "positionen"])
    for r in RECHNUNGEN:
        if not r["haushalt"]:
            continue  # bewusst fehlende Haushaltszeile (unvollstaendige Kette)
        ohne = set(r.get("ohne_betrag", []))
        summe = sum(kat[i]["preis"] for i in r["isbns"] if i not in ohne)
        pos = "; ".join(kat[i]["kurztitel"] for i in r["isbns"])
        ws.append([r["nr"], r["datum"], LIEFERANT, round(summe, 2), pos])
    ws.append([])
    ws.append([f"# {MARKER}"])
    # deterministische docProps
    wb.properties.created = DATUM_FIX
    wb.properties.modified = DATUM_FIX
    wb.properties.creator = "generieren.py"
    wb.properties.lastModifiedBy = "generieren.py"
    out = vdir / "haushalt.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    normalize_zip(out)


def gen_vermerke():
    ndir = ROOT / "notizen"
    kat = {b["isbn"]: b for b in KATALOG}
    for r in RECHNUNGEN:
        if not r["vermerk"]:
            continue
        titel = ", ".join(kat[i]["kurztitel"] for i in r["isbns"])
        md = (
            f"<!-- {MARKER} -->\n\n"
            f"# Vermerk zur Anschaffung {r['nr']}\n\n"
            f"Am {r['datum_fmt']} wurde die Rechnung **{r['nr']}** des Lieferanten "
            f"{LIEFERANT} verbucht. Sie betrifft die Titel: {titel}.\n\n"
            f"Die Anschaffung ist im Haushalt 2025 unter der Rechnungs-Nummer {r['nr']} "
            f"gefuehrt. Die zugehoerigen Katalogeintraege tragen dieselben ISBNs.\n"
        )
        schreibe_text(ndir / f"vermerk-{r['nr']}.md", md)
    # eine allgemeine Notiz mit z.B.-Falle (verfaelscht naive Satzzaehlung)
    schreibe_text(
        ndir / "arbeitshinweise.md",
        f"<!-- {MARKER} -->\n\n# Arbeitshinweise Erwerbung\n\n"
        "Belege werden zeitnah verbucht, z.B. Rechnungen und Lieferscheine. "
        "Bei Unklarheiten, z.B. fehlenden Betraegen, ist Ruecksprache zu halten.\n",
    )


def gen_magazin():
    mdir = ROOT / "magazin"
    mdir.mkdir(parents=True, exist_ok=True)
    for m in MAGAZIN:
        path = mdir / m["name"]
        if m["text"] is None:
            path.write_bytes(b"")  # 0-Byte-Datei (leerer Eintrag, Edge-Case)
            continue
        datum_hinweis = m["datum"] if m["datum"] else "ohne Datum"
        pdf_schreiben(path, [
            (ORG, 9, "Helvetica"),
            (m["text"], 12, "Helvetica-Bold"),
            (f"Datum: {datum_hinweis}", 10, "Helvetica"),
            ("", 6, "Helvetica"),
            (f"# {MARKER}", 7, "Helvetica"),
        ])


def gen_loesungen():
    ldir = ROOT / "loesungen"
    kat = {b["isbn"]: b for b in KATALOG}

    # 1) ISBN-Lookup Golden (Klartext OK: aus oeffentlicher Welt herleitbar)
    isbn_golden = {}
    for b in KATALOG:
        fx = lese_fixture(b["isbn"])
        isbn_golden[b["isbn"]] = {
            "titel": fx.get("title"),
            "autoren": [a.get("name") for a in fx.get("authors", [])],
            "jahr": fx.get("publish_date"),
        }
    schreibe_text(ldir / "isbn_lookup.golden.json",
                  json.dumps(isbn_golden, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    # 2) PDF-Extraktion Golden (Rechnungskopf + Betrag)
    pdf_golden = {}
    for r in RECHNUNGEN:
        ohne = set(r.get("ohne_betrag", []))
        summe = round(sum(kat[i]["preis"] for i in r["isbns"] if i not in ohne), 2)
        pdf_golden[r["nr"]] = {"datum_iso": r["datum"], "lieferant": LIEFERANT,
                               "betrag_eur": summe, "positionen": len(r["isbns"])}
    schreibe_text(ldir / "pdf_extraktion.golden.json",
                  json.dumps(pdf_golden, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    # 2b) DOI-Lookup Golden (Klartext OK: aus oeffentlicher Welt herleitbar)
    doi_golden = {}
    crdir = ROOT / "api-fixtures" / "crossref"
    for doi in DOIS:
        m = json.loads((crdir / f"{doi.replace('/', '_')}.json").read_text(encoding="utf-8")).get("message", {})
        jahr = None
        dp = m.get("issued", {}).get("date-parts", [[None]])
        if dp and dp[0]:
            jahr = dp[0][0]
        doi_golden[doi] = {"titel": (m.get("title") or [None])[0],
                           "container": (m.get("container-title") or [None])[0], "jahr": jahr}
    schreibe_text(ldir / "doi_lookup.golden.json",
                  json.dumps(doi_golden, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    # 2c) Pagination-Golden: die ueber rows/offset geblaetterten DOIs zu EINER Liste zusammengefuehrt
    suche_dois = []
    for seite in sorted(crdir.glob("suche_seite-*.json")):
        for it in json.loads(seite.read_text(encoding="utf-8")).get("message", {}).get("items", []):
            if it.get("DOI"):
                suche_dois.append(it["DOI"])
    schreibe_text(ldir / "doi_suche.golden.json", json.dumps({
        "verfahren": "Pagination ueber rows/offset: die drei Seiten zu einer Treffer-Liste zusammenfuehren.",
        "anzahl": len(suche_dois), "dois": suche_dois,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    # 3) Datei-Sortieren: Klartext-Mapping (E15(2): Datum steht ohnehin im oeffentlichen Datei-Inhalt).
    #    Soll = Datum je Datei bzw. "undatiert"; zusaetzlich ein Integritaets-Digest als Sekundaer-Check.
    mapping = {m["name"]: (m["datum"] if m["datum"] else "undatiert") for m in MAGAZIN}
    digest = hashlib.sha256(json.dumps(mapping, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    schreibe_text(ldir / "datei_sortieren.golden.json", json.dumps({
        "verfahren": "Soll-Datum je Datei (ISO) bzw. 'undatiert'. Die Pruefzelle vergleicht dein Mapping "
                     "Dateiname -> Datum gegen dieses Soll und benennt Abweichungen.",
        "mapping": mapping,
        "sammelordner_undatiert": sorted(n for n, d in mapping.items() if d == "undatiert"),
        "integritaets_sha256": digest,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    # 4) Verschlagwortung: Constraint-Manifest (kein exaktes Soll, E12)
    schreibe_text(ldir / "verschlagwortung.constraints.json", json.dumps({
        "verfahren": "Constraint-Pruefung (E12): jedes vergebene Schlagwort muss aus dem kontrollierten "
                     "Vokabular katalog/schlagworte.csv stammen; die Pflicht-Facetten muessen besetzt sein.",
        "vokabular": [k for k, _ in SCHLAGWORTE],
        "pflicht_facetten": PFLICHT_FACETTEN,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    # 5) README zum Verifikations-Layer
    schreibe_text(ldir / "README.md",
        f"<!-- {MARKER} -->\n\n# loesungen/ -- Verifikations-Layer\n\n"
        "Dieser Ordner ist öffentlich und dient dem Selbst-Check im Notebook. Die Sollwerte stehen "
        "im Klartext, weil sie ohnehin aus der öffentlichen Welt herleitbar sind: die Lookup-Ergebnisse "
        "aus den Fixtures, die Rechnungsbeträge aus den PDFs -- und auch das Soll-Datum beim "
        "Datei-Sortieren steht im Datei-Inhalt (Zeile 'Datum:'). Für das Datei-Sortieren liegt deshalb "
        "das vollständige Klartext-Mapping Dateiname -> Datum in datei_sortieren.golden.json; der "
        "zusätzliche integritaets_sha256 ist nur ein Sekundär-Check gegen versehentliche Veränderung, "
        "keine Verschleierung des Solls. Die Sollwerte des Berichtswesens (verwaltung/statistik/) stehen "
        "in statistik.golden.json: Anzahl, Summe, Mittelwert, Median, Minimum und Maximum, die "
        "Orange, R und Python gleich rechnen.\n")


# ------------------------------------------------------------------ Berichtswesen (verwaltung/statistik/)
# Erster Verbraucher: WBZ-Kurs fif10 "Statistik verstehen und visualisieren" (Orange, R, Python).
# Kanon: WELT.md, Abschnitt "Berichtswesen". Eigener Zufallsstrom (STAT_SEED), damit die Dateien
# der uebrigen Welt byte-gleich bleiben, egal was sich hier aendert. Alle Werte sind erfunden.
STAT_SEED = SEED + 1
STAT_JAHRE = [2022, 2023, 2024, 2025]
STAT_FORTSCHREIBUNG = (2026, 10)          # Januar bis Oktober 2026 als "neue Daten"
STANDORTE = {                             # Grundwerte je Monat 2022 (vor Saison und Trend)
    "Hauptstelle": {"besuche": 2400, "ausleihen": 1500, "fernleihe": 95, "kapazitaet": 3900},
    "Außenstelle": {"besuche": 650, "ausleihen": 380, "fernleihe": 22, "kapazitaet": 1050},
}
SAISON = {1: 1.00, 2: 0.97, 3: 1.04, 4: 1.08, 5: 1.06, 6: 0.93,
          7: 0.78, 8: 0.58, 9: 0.92, 10: 1.18, 11: 1.22, 12: 0.80}
TREND = {"besuche": 0.025, "ausleihen": -0.04, "fernleihe": -0.01}   # je Jahr
# Feste Luecken (WELT.md): Position aendert sich nie, damit Uebungen und loesungen stabil bleiben.
STAT_LUECKEN = {
    ("Außenstelle", "2024-06-01", "besuche"): "Zaehlgeraet defekt",
    ("Außenstelle", "2024-07-01", "besuche"): "Zaehlgeraet defekt",
    ("Außenstelle", "2024-08-01", "besuche"): "Zaehlgeraet defekt",
    ("Hauptstelle", "2023-11-01", "ausleihen"): "Systemumstellung im Ausleihsystem",
    ("Außenstelle", "2026-03-01", "besuche"): "Zaehlgeraet defekt",
}
MONATSNAMEN = ["jan", "feb", "mrz", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "dez"]
MONATSNAMEN_LANG = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
                    "September", "Oktober", "November", "Dezember"]
SCHULUNGEN = [  # name, Termine je Jahr, Gewichte Zufriedenheit 1..5, Gewichte Verstaendlichkeit 1..5
    ("Katalogrecherche", 6, [2, 4, 12, 42, 40], [2, 5, 15, 45, 33]),
    ("Datenbankrecherche", 4, [3, 6, 18, 43, 30], [5, 12, 28, 35, 20]),
    ("Fernleihe und Dokumentlieferung", 3, [2, 4, 14, 45, 35], [2, 6, 18, 44, 30]),
    ("Archivführung", 2, [1, 2, 7, 30, 60], [1, 3, 10, 36, 50]),
]
ZIELGRUPPEN = [("Studierende", 45), ("Beschäftigte", 35), ("Externe", 20)]
P_EMPFEHLUNG = {1: 0.10, 2: 0.25, 3: 0.55, 4: 0.85, 5: 0.97}
EVAL_LEERE_BOEGEN = ["EV-2023-021", "EV-2025-037"]   # vollstaendig leer abgegebene Boegen
FERNLEIHE_AUSREISSER = {2: 96, 6: 118, 9: 143}         # Monat 2025 -> Tage (je eine Buchbestellung Ausland)
STAT_HINWEIS = ("Fiktive Übungsdaten des messyverse (Bibliothek und Archiv des Instituts für "
                "Verwaltungs- und Regionalkunde, Berichtswesen). Alle Werte sind erfunden. "
                "Lizenz CC0 1.0.")


def stat_rng(teil):
    """Eigener, reproduzierbarer Zufallsstrom je Datenteil (Aenderung an einem Teil verschiebt keinen anderen)."""
    return random.Random(f"{STAT_SEED}-{teil}")


def stat_monate(bis=None):
    jahre = STAT_JAHRE if bis is None else [bis[0]]
    for j in jahre:
        for m in range(1, 13 if bis is None else bis[1] + 1):
            yield j, m


def stat_benutzung_zeilen(jahr_monate, rng):
    """Monatswerte je Standort. Gibt Zeilen als dict zurueck; Luecken als None."""
    zeilen = []
    for j, m in jahr_monate:
        t = (j - STAT_JAHRE[0]) + (m - 1) / 12
        monat = f"{j}-{m:02d}-01"
        for st, g in STANDORTE.items():
            def wert(art):
                return g[art] * SAISON[m] * (1 + TREND[art]) ** t * rng.gauss(1, 0.035)
            besuche = round(wert("besuche"))
            ausleihen = round(wert("ausleihen"))
            fernleihe = max(1, round(g["fernleihe"] * (1 + TREND["fernleihe"]) ** t
                                     * (0.6 + 0.4 * SAISON[m]) * rng.gauss(1, 0.08)))
            # Platzauslastung kommt aus der Sitzplatzbuchung, nicht vom Zaehlgeraet: sie bleibt auch
            # in Monaten mit fehlender Besuchszaehlung erhalten (Anker fuer eine modellbasierte Schaetzung).
            auslastung = round(min(98.0, besuche / g["kapazitaet"] * 100 * rng.gauss(1, 0.03)), 1)
            z = {"monat": monat, "jahr": j, "standort": st, "besuche": besuche,
                 "ausleihen": ausleihen, "fernleihbestellungen": fernleihe,
                 "platzauslastung": auslastung}
            for (lst, lmon, spalte) in STAT_LUECKEN:
                if lst == st and lmon == monat:
                    z[spalte] = None
            zeilen.append(z)
    return zeilen


BENUTZUNG_SPALTEN = ["monat", "jahr", "standort", "besuche", "ausleihen",
                     "fernleihbestellungen", "platzauslastung"]


def zelle_text(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)


def schreibe_csv(path, spalten, zeilen):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(spalten)
        for z in zeilen:
            w.writerow([zelle_text(z[s]) for s in spalten])


def speichere_xlsx(wb, path):
    wb.properties.created = DATUM_FIX
    wb.properties.modified = DATUM_FIX
    wb.properties.creator = "generieren.py"
    wb.properties.lastModifiedBy = "generieren.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    normalize_zip(path)


def hinweisblatt(wb, zusatz=""):
    ws = wb.create_sheet("Hinweis")
    ws.append([STAT_HINWEIS])
    if zusatz:
        ws.append([zusatz])
    ws.append([f"# {MARKER}"])


def schreibe_xlsx(path, spalten, zeilen, blattname="Daten"):
    """Saubere Excel-Fassung: Kopf in Zeile 1, Daten ab Zeile 2, Hinweis auf eigenem Blatt.
    Datumsangaben bleiben ISO-Text wie in der CSV, damit Orange beide Dateien gleich liest."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = blattname
    ws.append(spalten)
    for z in zeilen:
        ws.append([z[s] for s in spalten])
    hinweisblatt(wb)
    speichere_xlsx(wb, path)


def tausender(n):
    return f"{n:,}".replace(",", ".")


def gen_statistik():
    sdir = ROOT / "verwaltung" / "statistik"
    sdir.mkdir(parents=True, exist_ok=True)

    # 1) Monatswerte 2022-2025 und Fortschreibung 2026
    monatlich = stat_benutzung_zeilen(stat_monate(), stat_rng("benutzung"))
    neu = stat_benutzung_zeilen(stat_monate(STAT_FORTSCHREIBUNG), stat_rng("benutzung-2026"))
    for name, zeilen in [("benutzung_monatlich", monatlich), ("benutzung_2026", neu)]:
        schreibe_csv(sdir / f"{name}.csv", BENUTZUNG_SPALTEN, zeilen)
        schreibe_xlsx(sdir / f"{name}.xlsx", BENUTZUNG_SPALTEN, zeilen)

    # 2) Jahresverlauf der Besuche in Breitform (eine Zeile je Jahr und Standort)
    breit_spalten = ["jahr", "standort"] + MONATSNAMEN
    breit = []
    for j in STAT_JAHRE:
        for st in STANDORTE:
            z = {"jahr": j, "standort": st}
            for m, kurz in enumerate(MONATSNAMEN, 1):
                z[kurz] = next(r["besuche"] for r in monatlich
                               if r["standort"] == st and r["monat"] == f"{j}-{m:02d}-01")
            breit.append(z)
    schreibe_csv(sdir / "besuche_jahresverlauf.csv", breit_spalten, breit)
    schreibe_xlsx(sdir / "besuche_jahresverlauf.xlsx", breit_spalten, breit)

    # 3) Evaluation der Schulungen 2022-2025
    rng = stat_rng("evaluation")
    eval_spalten = ["bogen_nr", "datum", "jahr", "schulung", "zielgruppe",
                    "zufriedenheit", "verstaendlichkeit", "weiterempfehlung"]
    boegen = []
    for j in STAT_JAHRE:
        termine = []
        for name, anzahl, w_zuf, w_ver in SCHULUNGEN:
            monate = sorted(rng.sample([1, 2, 3, 4, 5, 6, 9, 10, 11, 12], anzahl))
            for m in monate:
                tag = rng.randint(2, 26)
                d = datetime(j, m, tag)
                while d.weekday() not in (1, 2, 3):   # Dienstag bis Donnerstag
                    d = d.replace(day=d.day + 1)
                termine.append((d.strftime("%Y-%m-%d"), name, w_zuf, w_ver))
        termine.sort()
        nr = 0
        for datum, name, w_zuf, w_ver in termine:
            for _ in range(rng.randint(3, 5)):
                nr += 1
                zg_gew = [g for _, g in ZIELGRUPPEN]
                if name == "Archivführung":
                    zg_gew = [30, 30, 40]
                zg = rng.choices([z for z, _ in ZIELGRUPPEN], weights=zg_gew)[0]
                zuf = rng.choices([1, 2, 3, 4, 5], weights=w_zuf)[0]
                ver = rng.choices([1, 2, 3, 4, 5], weights=w_ver)[0]
                emp = "ja" if rng.random() < P_EMPFEHLUNG[zuf] else "nein"
                extern = zg == "Externe"
                b = {"bogen_nr": f"EV-{j}-{nr:03d}", "datum": datum, "jahr": j, "schulung": name,
                     "zielgruppe": zg,
                     "zufriedenheit": None if rng.random() < 0.03 else zuf,
                     "verstaendlichkeit": None if rng.random() < (0.13 if extern else 0.05) else ver,
                     "weiterempfehlung": None if rng.random() < (0.20 if extern else 0.07) else emp}
                if b["bogen_nr"] in EVAL_LEERE_BOEGEN:
                    b.update(zufriedenheit=None, verstaendlichkeit=None, weiterempfehlung=None)
                boegen.append(b)
    schreibe_csv(sdir / "evaluation_schulungen.csv", eval_spalten, boegen)
    schreibe_xlsx(sdir / "evaluation_schulungen.xlsx", eval_spalten, boegen)

    # 4) Fernleihbestellungen der Aussenstelle 2025; Anzahl je Monat = benutzung_monatlich
    rng = stat_rng("fernleihe")
    fl_spalten = ["bestellnr", "bestelldatum", "monat", "lieferweg", "medium", "dauer_tage"]
    bestellungen = []
    median_tage = {("Inland", "Aufsatz"): 3, ("Inland", "Buch"): 8,
                   ("Ausland", "Aufsatz"): 6, ("Ausland", "Buch"): 19}
    for m in range(1, 13):
        monat = f"2025-{m:02d}-01"
        anzahl = next(r["fernleihbestellungen"] for r in monatlich
                      if r["standort"] == "Außenstelle" and r["monat"] == monat)
        letzter = (datetime(2025 + m // 12, m % 12 + 1, 1) - datetime(2025, m, 1)).days
        tage = sorted(rng.randint(1, letzter) for _ in range(anzahl))
        ausreisser = FERNLEIHE_AUSREISSER.get(m)
        for i, tag in enumerate(tage):
            weg = "Ausland" if rng.random() < 0.18 else "Inland"
            medium = "Aufsatz" if rng.random() < 0.40 else "Buch"
            dauer = max(1, round(median_tage[(weg, medium)] * math.exp(rng.gauss(0, 0.45))))
            if ausreisser and i == len(tage) // 2:
                weg, medium, dauer = "Ausland", "Buch", ausreisser
            bestellungen.append({"bestelldatum": f"2025-{m:02d}-{tag:02d}", "monat": monat,
                                 "lieferweg": weg, "medium": medium, "dauer_tage": dauer})
    for i, b in enumerate(bestellungen, 1):
        b["bestellnr"] = f"FL-A-2025-{i:04d}"
    schreibe_csv(sdir / "fernleihe_dauer.csv", fl_spalten, bestellungen)
    schreibe_xlsx(sdir / "fernleihe_dauer.xlsx", fl_spalten, bestellungen)

    # 5) Unordentlicher Export aus dem Bibliothekssystem (Uebung "sauber einlesen")
    #    Vorspann, Semikolon, Dezimalkomma, Tausenderpunkt, Punkt "." fuer fehlende Werte -- Datum bleibt
    #    ISO (JJJJ-MM). Der Punkt steht auf Oranges Fehlwertliste (owcsvimport.NA_DEFAULT); "k. A." stuende
    #    nicht darauf und machte die Spalte im CSV File Import unrettbar zu Text (gemessen 2026-11-11).
    #    weil Orange deutsche Datumsangaben beim CSV-Import still vertauscht (Tag <-> Monat).
    with (sdir / "benutzung_export.csv").open("w", encoding="utf-8", newline="") as f:
        f.write("Bibliothek und Archiv des Instituts für Verwaltungs- und Regionalkunde – "
                "Export Benutzungsstatistik\r\n")
        f.write(f"{STAT_HINWEIS} Erzeugt von generieren.py.\r\n")
        f.write("Monat;Standort;Besuche;Ausleihen;Fernleihbestellungen;Platzauslastung (%)\r\n")
        for z in monatlich:
            def feld(v):
                if v is None:
                    return "."
                if isinstance(v, float):
                    return f"{v:.1f}".replace(".", ",")
                return tausender(v)
            f.write(";".join([z["monat"][:7], z["standort"], feld(z["besuche"]), feld(z["ausleihen"]),
                              feld(z["fernleihbestellungen"]), feld(z["platzauslastung"])]) + "\r\n")

    # 6) Jahresbericht als Excel, wie er fuer einen Bericht gebaut wurde (Uebung "Excel aufraeumen")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Besuche"
    ws.append(["Jahresbericht Benutzung: Besuche je Monat (fiktive Übungsdaten)"])
    ws.append([])
    ws.append(["Jahr", "Standort"] + MONATSNAMEN_LANG + ["Summe"])
    spaltensummen = [0] * 12
    for z in breit:
        werte = [z[k] for k in MONATSNAMEN]
        for i, v in enumerate(werte):
            spaltensummen[i] += v or 0
        ws.append([z["jahr"], z["standort"]] + werte + [sum(v for v in werte if v is not None)])
    ws.append([])
    ws.append(["Summe", None] + spaltensummen + [sum(spaltensummen)])
    hinweisblatt(wb, "Leere Zellen: Zählgerät der Außenstelle Juni bis August 2024 defekt.")
    speichere_xlsx(wb, sdir / "jahresbericht_besuche.xlsx")

    # 7) README des Datenteils
    schreibe_text(sdir / "README.md", STAT_README.format(marker=MARKER, hinweis=STAT_HINWEIS))

    # 8) Sollwerte (loesungen/statistik.golden.json), gerechnet aus den geschriebenen CSV-Dateien
    golden = statistik_sollwerte(sdir)
    schreibe_text(ROOT / "loesungen" / "statistik.golden.json",
                  json.dumps(golden, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return golden


def lies_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def zahl(s):
    return None if s == "" else (float(s) if "." in s else int(s))


def statistik_sollwerte(sdir):
    """Sollwerte fuer Uebungen und Abgleich Orange/R/Python. Nur Mittelwert, Median, Summe,
    Anzahl, Minimum, Maximum: diese rechnen alle drei Werkzeuge gleich (keine Quantil-Varianten)."""
    import statistics as stx

    def kennwerte(werte):
        w = [v for v in werte if v is not None]
        return {"n": len(w), "fehlend": len(werte) - len(w), "summe": round(sum(w), 2),
                "mittelwert": round(stx.mean(w), 2), "median": stx.median(w),
                "min": min(w), "max": max(w)}

    out = {"verfahren": "Sollwerte aus den CSV-Dateien unter verwaltung/statistik/, gerechnet von "
                        "generieren.py (Python statistics). Fehlende Werte zaehlen nicht mit. "
                        "Mittelwerte auf zwei Nachkommastellen gerundet."}
    for name in ["benutzung_monatlich", "benutzung_2026"]:
        z = lies_csv(sdir / f"{name}.csv")
        teil = {"zeilen": len(z), "spalten": list(z[0].keys())}
        for spalte in ["besuche", "ausleihen", "fernleihbestellungen", "platzauslastung"]:
            teil[spalte] = {}
            for st in STANDORTE:
                teil[spalte][st] = kennwerte([zahl(r[spalte]) for r in z if r["standort"] == st])
            teil[spalte]["je_jahr_und_standort_summe"] = {
                f"{j}|{st}": round(sum(v for v in (zahl(r[spalte]) for r in z
                                                  if r["jahr"] == str(j) and r["standort"] == st)
                                       if v is not None), 2)
                for j in sorted({int(r["jahr"]) for r in z}) for st in STANDORTE}
        teil["luecken"] = sorted(f"{r['standort']}|{r['monat']}|{s}" for r in z
                                 for s in BENUTZUNG_SPALTEN if r[s] == "")
        out[name] = teil
    z = lies_csv(sdir / "benutzung_monatlich.csv")
    sommer = {}
    for j in STAT_JAHRE:
        werte = [zahl(r["besuche"]) for r in z if r["standort"] == "Außenstelle" and r["jahr"] == str(j)
                 and r["monat"][5:7] in ("06", "07", "08")]
        sommer[str(j)] = None if None in werte else round(stx.mean(werte), 2)
    out["benutzung_monatlich"]["aussenstelle_besuche_sommermittel_jun_aug"] = sommer
    kz = {}
    for j in STAT_JAHRE:
        rs = [r for r in z if r["standort"] == "Hauptstelle" and r["jahr"] == str(j)
              and r["ausleihen"] != "" and r["besuche"] != ""]
        kz[str(j)] = round(sum(int(r["ausleihen"]) for r in rs) / sum(int(r["besuche"]) for r in rs) * 100, 2)
    out["benutzung_monatlich"]["hauptstelle_ausleihen_je_100_besuche_je_jahr"] = kz

    fl = lies_csv(sdir / "fernleihe_dauer.csv")
    out["fernleihe_dauer"] = {"zeilen": len(fl), "dauer_tage": kennwerte([int(r["dauer_tage"]) for r in fl])}
    for gruppe in ["lieferweg", "medium"]:
        out["fernleihe_dauer"][f"nach_{gruppe}"] = {
            g: kennwerte([int(r["dauer_tage"]) for r in fl if r[gruppe] == g])
            for g in sorted({r[gruppe] for r in fl})}
    out["fernleihe_dauer"]["ueber_30_tage"] = sum(int(r["dauer_tage"]) > 30 for r in fl)
    out["fernleihe_dauer"]["ueber_90_tage"] = sum(int(r["dauer_tage"]) > 90 for r in fl)

    ev = lies_csv(sdir / "evaluation_schulungen.csv")
    out["evaluation_schulungen"] = {"zeilen": len(ev)}
    for spalte in ["zufriedenheit", "verstaendlichkeit"]:
        out["evaluation_schulungen"][spalte] = kennwerte([zahl(r[spalte]) for r in ev])
        out["evaluation_schulungen"][spalte]["nach_schulung"] = {
            s: kennwerte([zahl(r[spalte]) for r in ev if r["schulung"] == s])
            for s, *_ in SCHULUNGEN}
    emp = [r["weiterempfehlung"] for r in ev]
    out["evaluation_schulungen"]["weiterempfehlung"] = {
        "ja": emp.count("ja"), "nein": emp.count("nein"), "fehlend": emp.count(""),
        "anteil_ja_unter_antworten": round(emp.count("ja") / (emp.count("ja") + emp.count("nein")), 2)}
    out["evaluation_schulungen"]["fehlend_nach_zielgruppe"] = {
        zg: {s: sum(r[s] == "" for r in ev if r["zielgruppe"] == zg)
             for s in ["zufriedenheit", "verstaendlichkeit", "weiterempfehlung"]}
        for zg, _ in ZIELGRUPPEN}
    out["evaluation_schulungen"]["zeilen_nach_zielgruppe"] = {
        zg: sum(r["zielgruppe"] == zg for r in ev) for zg, _ in ZIELGRUPPEN}
    out["evaluation_schulungen"]["leere_boegen"] = sorted(
        r["bogen_nr"] for r in ev if r["zufriedenheit"] == r["verstaendlichkeit"] == r["weiterempfehlung"] == "")
    return out


STAT_README = """<!-- {marker} -->

# verwaltung/statistik/ -- Berichtswesen der Bibliothek

{hinweis}

Das Berichtswesen sammelt die Zahlen, die die Verwaltung jeden Monat zusammenträgt und einmal im Jahr berichtet. Die Dateien liegen als CSV (UTF-8, Komma, Punkt als Dezimalzeichen, Datum als JJJJ-MM-TT) und als Excel-Datei mit demselben Inhalt vor; die Excel-Fassung trägt den Hinweis auf fiktive Daten auf dem zweiten Blatt „Hinweis“. Leere Zellen sind fehlende Werte. Kanon und Begründung: WELT.md, Abschnitt „Berichtswesen“; Sollwerte: loesungen/statistik.golden.json.

| Datei | Inhalt |
|---|---|
| `benutzung_monatlich` | Januar 2022 bis Dezember 2025, je Monat und Standort (Hauptstelle, Außenstelle): `besuche` (Eingangszählung), `ausleihen`, `fernleihbestellungen`, `platzauslastung` (Lesesaal, Prozent aus der Sitzplatzbuchung) |
| `benutzung_2026` | dieselben Spalten für Januar bis Oktober 2026 |
| `besuche_jahresverlauf` | die Besuche aus `benutzung_monatlich` in Breitform: eine Zeile je Jahr und Standort, Spalten `jan` bis `dez` |
| `evaluation_schulungen` | Rückmeldebögen zu vier Schulungen 2022 bis 2025: `zielgruppe`, `zufriedenheit` und `verstaendlichkeit` von 1 (gar nicht) bis 5 (sehr), `weiterempfehlung` ja/nein; unbeantwortete Fragen bleiben leer |
| `fernleihe_dauer` | alle Fernleihbestellungen der Außenstelle 2025 mit `lieferweg`, `medium` und `dauer_tage` (Tage bis zur Bereitstellung); die Anzahl je Monat entspricht `fernleihbestellungen` der Außenstelle |
| `benutzung_export.csv` | `benutzung_monatlich` als unordentlicher Systemexport: zwei Vorspannzeilen, Semikolon, Dezimalkomma, Tausenderpunkt, ein Punkt „.“ für fehlende Werte |
| `jahresbericht_besuche.xlsx` | `besuche_jahresverlauf` als Berichtstabelle: Titelzeile, Leerzeile, Summenspalte, Summenzeile, Hinweisblatt |

Bekannte Lücken (feste Positionen): Besuche der Außenstelle Juni bis August 2024 und März 2026 (Zählgerät defekt), Ausleihen der Hauptstelle November 2023 (Systemumstellung).
"""


def pruefe_integritaet():
    """E2-Assertions: Schluessel-Eindeutigkeit + Ketten-Bilanz."""
    isbns = [b["isbn"] for b in KATALOG]
    assert len(isbns) == len(set(isbns)), "ISBN nicht eindeutig im Katalog"
    nrs = [r["nr"] for r in RECHNUNGEN]
    assert len(nrs) == len(set(nrs)), "Rechnungs-Nummer nicht eindeutig"
    kat = set(isbns)
    in_rechnung = {i for r in RECHNUNGEN for i in r["isbns"]}
    assert in_rechnung <= kat, "Rechnung referenziert ISBN ausserhalb des Katalogs"
    kein_beleg = kat - in_rechnung
    ohne_haushalt = [r["nr"] for r in RECHNUNGEN if not r["haushalt"]]
    ohne_betrag = [i for r in RECHNUNGEN for i in r.get("ohne_betrag", [])]
    voll = sum(1 for r in RECHNUNGEN if r["haushalt"] and r["vermerk"] and not r.get("ohne_betrag"))
    print(f"  Integritaet OK: {len(isbns)} Titel, {len(nrs)} Rechnungen")
    print(f"  vollstaendige Ketten: {voll} Rechnungen")
    print(f"  unvollstaendig: kein_beleg={sorted(kein_beleg)} ohne_haushalt={ohne_haushalt} ohne_betrag={ohne_betrag}")
    # genau die geplanten Unvollstaendigkeiten
    assert len(kein_beleg) >= 1, "kein belegfreier Katalogeintrag -> Lernanlass fehlt"
    assert ohne_haushalt, "keine Rechnung ohne Haushaltszeile"
    assert ohne_betrag, "keine Rechnung ohne Betragszeile"


def main():
    rng_pin()  # Seed gepinnt (aktuell nutzt die Generierung feste Werte; RNG bleibt der Anker)
    print("messyverse-Generator")
    pruefe_integritaet()
    # frische, deterministische Ausgabe: erzeugte Welt-Ordner leeren (Fixtures bleiben)
    for d in ["katalog", "erwerbung", "verwaltung", "notizen", "magazin", "loesungen"]:
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p)
    gen_katalog();      print("  katalog/ geschrieben")
    gen_rechnungen();   print("  erwerbung/ (PDF) geschrieben")
    gen_haushalt();     print("  verwaltung/haushalt.xlsx geschrieben")
    gen_vermerke();     print("  notizen/ geschrieben")
    gen_magazin();      print("  magazin/ geschrieben")
    gen_loesungen();    print("  loesungen/ geschrieben")
    gen_statistik();    print("  verwaltung/statistik/ + loesungen/statistik.golden.json geschrieben")
    print("Fertig.")


if __name__ == "__main__":
    main()
