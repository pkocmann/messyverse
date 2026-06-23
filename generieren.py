#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""generieren.py -- seed-fester Generator des messyverse-Uebungsuniversums.

Baut das komplette Welt-Universum reproduzierbar aus den gepinnten API-Fixtures
(api-fixtures/, Wahrheitsquelle fuer die Bibliografie). Dieser Generator geht
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
    # isbns.txt
    schreibe_text(kdir / "isbns.txt", f"# {MARKER}\n" + "\n".join(b["isbn"] for b in KATALOG) + "\n")
    # dois.txt
    schreibe_text(kdir / "dois.txt", f"# {MARKER}\n" + "\n".join(DOIS) + "\n")
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

    # 3) Datei-Sortieren: Digest-first (E15) -- nur Hash des Soll-Endzustands + undatiert-Liste,
    #    NICHT die Antwortzuordnung selbst.
    soll = []
    undatiert = []
    for m in MAGAZIN:
        if m["datum"] is None:
            undatiert.append(m["name"])
        else:
            # Soll-Zielname: JJJJ-MM-TT__<vorgang-slug>.pdf
            slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in (m["text"] or "datei")).strip("-")[:24]
            soll.append(f"{m['datum']}__{slug}.pdf")
    soll_sorted = sorted(soll)
    digest = hashlib.sha256(("\n".join(soll_sorted)).encode("utf-8")).hexdigest()
    schreibe_text(ldir / "datei_sortieren.manifest.json", json.dumps({
        "verfahren": "Digest-first (E15): committet wird nur der SHA-256 des sortierten Soll-Endzustands, "
                     "nicht die Zuordnung. Die Pruefzelle bildet denselben Digest ueber den TN-Output.",
        "soll_anzahl_datierbar": len(soll_sorted),
        "soll_sha256": digest,
        "sammelordner_undatiert": sorted(undatiert),
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
        "Dieser Ordner ist oeffentlich und dient dem Selbst-Check im Notebook. Fuer Aufgaben, bei denen "
        "das Ergebnis zugleich die Loesung waere (Datei-Sortieren), wird nur ein **Digest** des "
        "Soll-Endzustands hinterlegt (nicht rueckrechenbar). Wo der Sollwert ohnehin aus der oeffentlichen "
        "Welt herleitbar ist (Lookup-Ergebnisse, Rechnungsbetraege), steht er im Klartext.\n")


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
    print("Fertig.")


if __name__ == "__main__":
    main()
