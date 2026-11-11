# SPDX-License-Identifier: MIT
"""Regressionstest des Berichtswesens verwaltung/statistik/ (Kanon: WELT.md, Abschnitt "Berichtswesen").

Geprueft werden die AUSGELIEFERTEN Dateien, nicht der Generator-Code allein: Reproduzierbarkeit in
einer Wegwerf-Kopie, Gleichheit von CSV und Excel, feste Luecken, die gestalteten Eigenschaften,
die die Kursuebungen tragen, die zwei unordentlichen Dateien und die Sollwerte.

Aufruf aus dem Repo-Wurzelverzeichnis:  python tests/test_statistik.py
"""
import csv
import hashlib
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

import openpyxl

WURZEL = Path(__file__).resolve().parent.parent
SDIR = WURZEL / "verwaltung" / "statistik"
sys.path.insert(0, str(WURZEL))
import generieren as gen  # noqa: E402

# Unabhaengige Erwartungen aus WELT.md, Abschnitt "Berichtswesen" -- bewusst NICHT aus generieren.py
# uebernommen, damit eine falsche Generator-Aenderung samt Regeneration auffaellt.
KANON_LUECKEN = {
    ("Außenstelle", "2024-06-01", "besuche"), ("Außenstelle", "2024-07-01", "besuche"),
    ("Außenstelle", "2024-08-01", "besuche"), ("Hauptstelle", "2023-11-01", "ausleihen"),
    ("Außenstelle", "2026-03-01", "besuche"),
}
KANON_LEERE_BOEGEN = ["EV-2023-021", "EV-2025-037"]
KANON_STANDORTE = ["Hauptstelle", "Außenstelle"]
SAUBER = ["benutzung_monatlich", "benutzung_2026", "besuche_jahresverlauf",
          "evaluation_schulungen", "fernleihe_dauer"]
WELTORDNER = ["katalog", "erwerbung", "verwaltung", "notizen", "magazin", "loesungen"]
ERGEBNISSE = []


def pruefe(name, bedingung, detail=""):
    ERGEBNISSE.append(bool(bedingung))
    print(f"  [{'OK ' if bedingung else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not bedingung else ""))


def csv_zeilen(name):
    with (SDIR / f"{name}.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def xlsx_zeilen(name):
    wb = openpyxl.load_workbook(SDIR / f"{name}.xlsx", data_only=True)
    ws = wb.worksheets[0]
    werte = list(ws.iter_rows(values_only=True))
    kopf = [str(k) for k in werte[0]]
    return kopf, [dict(zip(kopf, z)) for z in werte[1:]], wb


def als_text(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)


def gleicher_wert(xlsx_wert, csv_text):
    if isinstance(xlsx_wert, (int, float)) and not isinstance(xlsx_wert, bool):
        return csv_text != "" and float(csv_text) == float(xlsx_wert)
    return als_text(xlsx_wert) == csv_text


def zahl(s):
    return None if s == "" else float(s)


def baum_hashes(wurzel):
    out = {}
    for ordner in WELTORDNER:
        for p in sorted((wurzel / ordner).rglob("*")):
            if p.is_file():
                out[p.relative_to(wurzel).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_reproduzierbar():
    print("Reproduzierbarkeit (Generator in einer Wegwerf-Kopie):")
    with tempfile.TemporaryDirectory() as tmp:
        kopie = Path(tmp) / "messyverse"
        shutil.copytree(WURZEL, kopie, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
        r = subprocess.run([sys.executable, "generieren.py"], cwd=kopie, capture_output=True, text=True)
        pruefe("Generator laeuft ohne Fehler", r.returncode == 0, r.stderr[-300:])
        soll, ist = baum_hashes(WURZEL), baum_hashes(kopie)
        abweichend = sorted(k for k in soll.keys() | ist.keys() if soll.get(k) != ist.get(k))
        pruefe(f"alle {len(soll)} Weltdateien byte-gleich", not abweichend, ", ".join(abweichend[:5]))


def test_csv_gleich_excel():
    print("CSV und Excel mit gleichem Inhalt:")
    for name in SAUBER:
        c = csv_zeilen(name)
        kopf, x, wb = xlsx_zeilen(name)
        # Zahlen numerisch vergleichen: Excel speichert 68.0 als 68, der Wert ist derselbe.
        gleich = kopf == list(c[0].keys()) and len(c) == len(x) and all(
            gleicher_wert(xz[k], cz[k]) for cz, xz in zip(c, x) for k in kopf)
        pruefe(f"{name}: {len(c)} Zeilen, Kopf und Werte gleich", gleich)
        pruefe(f"{name}.xlsx: Blatt 1 'Daten', Blatt 2 'Hinweis' mit Fiktiv-Hinweis",
               wb.sheetnames == ["Daten", "Hinweis"] and wb["Hinweis"]["A1"].value == gen.STAT_HINWEIS)


def test_luecken():
    print("Feste Luecken:")
    for name, jahre in [("benutzung_monatlich", "2022-2025"), ("benutzung_2026", "2026")]:
        z = csv_zeilen(name)
        ist = {(r["standort"], r["monat"], s) for r in z for s in gen.BENUTZUNG_SPALTEN if r[s] == ""}
        soll = {k for k in KANON_LUECKEN if k[1][:4] in ({"2026"} if jahre == "2026"
                                                          else {"2022", "2023", "2024", "2025"})}
        pruefe(f"{name}: Luecken genau an den festen Stellen ({len(soll)})", ist == soll, str(ist ^ soll))
    breit = csv_zeilen("besuche_jahresverlauf")
    leer = {(r["jahr"], r["standort"], m) for r in breit for m in gen.MONATSNAMEN if r[m] == ""}
    pruefe("besuche_jahresverlauf: leer nur Aussenstelle 2024 jun/jul/aug",
           leer == {("2024", "Außenstelle", m) for m in ("jun", "jul", "aug")}, str(leer))
    z = csv_zeilen("benutzung_monatlich")
    pruefe("Platzauslastung auch in Luecken-Monaten vorhanden", all(r["platzauslastung"] != "" for r in z))


def test_kalender():
    print("Kalender und Schluessel:")
    from datetime import date
    for name, monate in [("benutzung_monatlich", [(j, m) for j in range(2022, 2026) for m in range(1, 13)]),
                         ("benutzung_2026", [(2026, m) for m in range(1, 11)])]:
        z = csv_zeilen(name)
        soll = [(f"{j}-{m:02d}-01", st) for j, m in monate for st in KANON_STANDORTE]
        pruefe(f"{name}: lueckenloses Monatsraster, Reihenfolge Monat/Standort, Schluessel eindeutig",
               [(r["monat"], r["standort"]) for r in z] == soll)
        pruefe(f"{name}: jahr passt zum Monat", all(r["jahr"] == r["monat"][:4] for r in z))
    fl = csv_zeilen("fernleihe_dauer")
    try:
        ok = all(date.fromisoformat(r["bestelldatum"]).isoformat()[:7] == r["monat"][:7] for r in fl)
    except ValueError:
        ok = False
    pruefe("fernleihe_dauer: Bestelldatum ist ein gueltiges Datum im angegebenen Monat", ok)
    ev = csv_zeilen("evaluation_schulungen")
    try:
        ok = all(date.fromisoformat(r["datum"]).weekday() in (1, 2, 3) and r["jahr"] == r["datum"][:4] for r in ev)
    except ValueError:
        ok = False
    pruefe("evaluation_schulungen: Termine gueltig, Dienstag bis Donnerstag, jahr passt", ok)
    from datetime import datetime
    d = gen.stat_werktag_im_monat(datetime(2022, 2, 26))
    pruefe("Randfall Februarende: Termin bleibt im Februar und faellt auf Di bis Do",
           d.month == 2 and d.weekday() in (1, 2, 3), d.isoformat())


def test_lang_breit():
    print("Lang- und Breitform:")
    lang = {(r["jahr"], r["standort"], r["monat"][5:7]): r["besuche"] for r in csv_zeilen("benutzung_monatlich")}
    breit = csv_zeilen("besuche_jahresverlauf")
    pruefe("Breitform: Kopf jahr, standort, jan bis dez", list(breit[0].keys()) ==
           ["jahr", "standort", "jan", "feb", "mrz", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "dez"])
    pruefe("Breitform: Zeilen je Jahr und Standort in fester Reihenfolge",
           [(r["jahr"], r["standort"]) for r in breit] == [(str(j), st) for j in range(2022, 2026) for st in KANON_STANDORTE])
    namen = list(breit[0].keys())[2:]
    pruefe("Breitform aus Langform unabhaengig rekonstruiert, alle 96 Zellen gleich",
           all(r[n] == lang[(r["jahr"], r["standort"], f"{i:02d}")] for r in breit for i, n in enumerate(namen, 1)))


def test_eigenschaften():
    print("Gestaltete Eigenschaften:")
    z = csv_zeilen("benutzung_monatlich")

    def summe(st, j, sp):
        return sum(int(r[sp]) for r in z if r["standort"] == st and r["jahr"] == str(j) and r[sp] != "")
    a = [summe("Hauptstelle", j, "ausleihen") for j in gen.STAT_JAHRE]
    b = [summe("Hauptstelle", j, "besuche") for j in gen.STAT_JAHRE]
    pruefe("Hauptstelle: Ausleihen 2025 unter 2022, auch 2024 unter 2022", a[3] < a[0] and a[2] < a[0], str(a))
    a2 = [summe("Außenstelle", j, "ausleihen") for j in gen.STAT_JAHRE]
    pruefe("Aussenstelle: Ausleihen sinken jedes Jahr", all(x > y for x, y in zip(a2, a2[1:])), str(a2))
    pruefe("Hauptstelle: Besuche steigen jedes Jahr", all(x < y for x, y in zip(b, b[1:])), str(b))
    ok_min, ok_max = True, True
    for st in gen.STANDORTE:
        for j in gen.STAT_JAHRE:
            v = {r["monat"][5:7]: int(r["besuche"]) for r in z
                 if r["standort"] == st and r["jahr"] == str(j) and r["besuche"] != ""}
            if len(v) == 12:
                ok_min &= min(v, key=v.get) == "08"
                ok_max &= max(v, key=v.get) in ("10", "11")
    pruefe("vollstaendige Jahre: August ruhigster Monat", ok_min)
    pruefe("vollstaendige Jahre: Oktober oder November vollster Monat", ok_max)
    sommer = [int(r["besuche"]) for r in z if r["standort"] == "Außenstelle"
              and r["monat"][5:7] in ("06", "07", "08") and r["besuche"] != ""]
    alle = [int(r["besuche"]) for r in z if r["standort"] == "Außenstelle" and r["besuche"] != ""]
    pruefe("Aussenstelle: jeder vorhandene Sommerwert unter dem Mittelwert aller Monate",
           max(sommer) < statistics.mean(alle), f"{max(sommer)} vs {statistics.mean(alle):.1f}")


def test_fernleihe():
    print("Fernleihe:")
    fl = csv_zeilen("fernleihe_dauer")
    z = csv_zeilen("benutzung_monatlich")
    soll = {r["monat"]: int(r["fernleihbestellungen"]) for r in z
            if r["standort"] == "Außenstelle" and r["jahr"] == "2025"}
    ist = {}
    for r in fl:
        ist[r["monat"]] = ist.get(r["monat"], 0) + 1
    pruefe("Anzahl je Monat = fernleihbestellungen der Aussenstelle 2025", ist == soll)
    pruefe("Bestelldatum liegt im angegebenen Monat", all(r["bestelldatum"][:7] == r["monat"][:7] for r in fl))
    pruefe("Bestellnummern fortlaufend", [r["bestellnr"] for r in fl] ==
           [f"FL-A-2025-{i:04d}" for i in range(1, len(fl) + 1)])
    d = [int(r["dauer_tage"]) for r in fl]
    pruefe("rechtsschief: Mittelwert mindestens 30 % ueber dem Median",
           statistics.mean(d) >= 1.3 * statistics.median(d), f"{statistics.mean(d):.2f} / {statistics.median(d)}")
    lang = [r for r in fl if int(r["dauer_tage"]) > 90]
    pruefe("genau drei Bestellungen ueber 90 Tage, alle Ausland/Buch",
           len(lang) == 3 and all(r["lieferweg"] == "Ausland" and r["medium"] == "Buch" for r in lang))
    pruefe("Dauer mindestens 1 Tag", min(d) >= 1)


def test_evaluation():
    print("Evaluation:")
    ev = csv_zeilen("evaluation_schulungen")
    pruefe("Bogennummern eindeutig", len({r["bogen_nr"] for r in ev}) == len(ev))
    leer = sorted(r["bogen_nr"] for r in ev if r["zufriedenheit"] == r["verstaendlichkeit"]
                  == r["weiterempfehlung"] == "")
    pruefe("genau die zwei festen leeren Boegen", leer == KANON_LEERE_BOEGEN, str(leer))
    pruefe("Bewertungen nur 1 bis 5 oder leer", all(r[s] in ("", "1", "2", "3", "4", "5")
                                                    for r in ev for s in ("zufriedenheit", "verstaendlichkeit")))
    pruefe("Weiterempfehlung nur ja, nein oder leer", {r["weiterempfehlung"] for r in ev} <= {"ja", "nein", ""})

    def quote(zg):
        g = [r for r in ev if r["zielgruppe"] == zg]
        return sum(r["weiterempfehlung"] == "" for r in g) / len(g)
    pruefe("Externe lassen die Weiterempfehlung haeufiger offen",
           quote("Externe") > max(quote("Studierende"), quote("Beschäftigte")))
    for s in ("zufriedenheit", "verstaendlichkeit"):
        w = [int(r[s]) for r in ev if r[s]]
        pruefe(f"{s}: Bewertungen haeufen sich bei 4 und 5", sum(v >= 4 for v in w) / len(w) > 0.6)


def test_export_csv():
    print("Unordentlicher Export:")
    # Rohbytes lesen: read_text wuerde die Zeilenenden CRLF zu LF normalisieren.
    roh = (SDIR / "benutzung_export.csv").read_bytes().decode("utf-8")
    zeilen = roh.split("\r\n")
    pruefe("Zeilenende CRLF, zwei Vorspannzeilen, Fiktiv-Hinweis im Vorspann",
           "\n" not in roh.replace("\r\n", "") and "Fiktive" in zeilen[1] and ";" not in zeilen[0])
    kopf = zeilen[2].split(";")
    pruefe("Kopf mit Semikolon, sechs Spalten", len(kopf) == 6, str(kopf))
    daten = [z.split(";") for z in zeilen[3:] if z]
    sauber = csv_zeilen("benutzung_monatlich")

    def zurueck(feld):
        if feld == ".":
            return ""
        if "," in feld:
            return feld.replace(",", ".")
        return feld.replace(".", "")
    gleich = len(daten) == len(sauber) and all(
        d[0] == s["monat"][:7] and d[1] == s["standort"]
        and [zurueck(x) for x in d[2:]] == [s["besuche"], s["ausleihen"], s["fernleihbestellungen"],
                                            s["platzauslastung"]]
        for d, s in zip(daten, sauber))
    pruefe("mit Semikolon, Dezimalkomma, Tausenderpunkt und Punkt gelesen = benutzung_monatlich", gleich)
    felder = [f for d in daten for f in d[2:]]
    pruefe("Fehlwert-Punkt genau so oft wie Luecken", felder.count(".") == sum(
        r[s] == "" for r in sauber for s in gen.BENUTZUNG_SPALTEN))


def test_jahresbericht():
    print("Unordentlicher Jahresbericht:")
    wb = openpyxl.load_workbook(SDIR / "jahresbericht_besuche.xlsx", data_only=True)
    ws = wb["Besuche"]
    w = list(ws.iter_rows(values_only=True))
    pruefe("Blaetter 'Besuche' und 'Hinweis'", wb.sheetnames == ["Besuche", "Hinweis"])
    pruefe("Titel in A1, Zeile 2 leer, Kopf in Zeile 3",
           str(w[0][0]).startswith("Jahresbericht") and all(v is None for v in w[1])
           and w[2][0] == "Jahr" and w[2][-1] == "Summe")
    daten = w[3:11]
    breit = csv_zeilen("besuche_jahresverlauf")
    pruefe("Kopf: Jahr, Standort, zwoelf Monatsnamen, Summe", list(w[2]) == ["Jahr", "Standort",
           "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
           "Oktober", "November", "Dezember", "Summe"])
    pruefe("acht Datenzeilen = besuche_jahresverlauf, mit Jahr und Standort", len(daten) == 8 and all(
        str(d[0]) == b["jahr"] and d[1] == b["standort"] and
        all(gleicher_wert(v, b[m]) if v is not None else b[m] == "" for v, m in zip(d[2:14], gen.MONATSNAMEN))
        for d, b in zip(daten, breit)))
    pruefe("Summenspalte = Zeilensumme", all(d[14] == sum(v for v in d[2:14] if v is not None) for d in daten))
    summe = w[12]
    pruefe("Summenzeile = Spaltensummen, Gesamtsumme = Summe aller Zellen", summe[0] == "Summe" and all(
        summe[2 + i] == sum((d[2 + i] or 0) for d in daten) for i in range(12))
        and summe[14] == sum((v or 0) for d in daten for v in d[2:14]))


def test_sollwerte():
    print("Sollwerte:")
    datei = json.loads((WURZEL / "loesungen" / "statistik.golden.json").read_text(encoding="utf-8"))
    neu = json.loads(json.dumps(gen.statistik_sollwerte(SDIR), ensure_ascii=False, sort_keys=True))
    pruefe("statistik.golden.json = Neuberechnung aus den CSV-Dateien", datei == neu)
    fl = [int(r["dauer_tage"]) for r in csv_zeilen("fernleihe_dauer")]
    pruefe("Stichprobe unabhaengig gerechnet: Median und Mittelwert der Fernleihdauer",
           datei["fernleihe_dauer"]["dauer_tage"]["median"] == statistics.median(fl)
           and datei["fernleihe_dauer"]["dauer_tage"]["mittelwert"] == round(statistics.mean(fl), 2))
    # Unabhaengig gerechnet: Kennzahl und Vergleich gleicher Monate (eigene Rechenwege, nicht gen.*)
    z = csv_zeilen("benutzung_monatlich")
    hs23 = [r for r in z if r["standort"] == "Hauptstelle" and r["jahr"] == "2023" and r["ausleihen"] and r["besuche"]]
    kz = datei["benutzung_monatlich"]["hauptstelle_ausleihen_je_100_besuche"]
    pruefe("Kennzahl 2023: 11 Monate, Jahresmittel der Monatswerte und Verhaeltnis der Summen",
           kz["monate_mit_kennzahl"]["2023"] == len(hs23) == 11
           and kz["jahresmittel_der_monatswerte"]["2023"] == round(statistics.mean(
               int(r["ausleihen"]) / int(r["besuche"]) * 100 for r in hs23), 2)
           and kz["verhaeltnis_der_summen_gemeinsamer_monate"]["2023"] == round(
               sum(int(r["ausleihen"]) for r in hs23) / sum(int(r["besuche"]) for r in hs23) * 100, 2))
    z26 = csv_zeilen("benutzung_2026")
    v = datei["vergleich_gleicher_monate_2025_2026"]
    pruefe("Vergleich Januar bis Oktober: Hauptstelle Besuche 2025 und 2026 unabhaengig gerechnet",
           v["2025|Hauptstelle|besuche"]["summe"] == sum(int(r["besuche"]) for r in z if r["standort"] == "Hauptstelle"
                                                       and r["jahr"] == "2025" and r["monat"][5:7] <= "10")
           and v["2026|Hauptstelle|besuche"]["summe"] == sum(int(r["besuche"]) for r in z26 if r["standort"] == "Hauptstelle"))
    pruefe("keine Jahressummen von Prozentwerten",
           "je_jahr_und_standort_summe" not in datei["benutzung_monatlich"]["platzauslastung"])
    readme = (SDIR / "README.md").read_text(encoding="utf-8")
    pruefe("README kennzeichnet die Daten als erfunden, mit SPDX CC0-1.0 und Marker",
           "erfunden" in readme and "SPDX-License-Identifier: CC0-1.0" in readme and gen.MARKER in readme)


if __name__ == "__main__":
    for t in [test_reproduzierbar, test_csv_gleich_excel, test_luecken, test_kalender, test_lang_breit,
              test_eigenschaften,
              test_fernleihe, test_evaluation, test_export_csv, test_jahresbericht, test_sollwerte]:
        t()
        print()
    fehler = ERGEBNISSE.count(False)
    print(f"{len(ERGEBNISSE)} Pruefungen, {'ALLE BESTANDEN' if not fehler else f'{fehler} FEHLGESCHLAGEN'}")
    sys.exit(1 if fehler else 0)
