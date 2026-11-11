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
        soll = {k for k in gen.STAT_LUECKEN if k[1][:4] in ({"2026"} if jahre == "2026"
                                                            else {"2022", "2023", "2024", "2025"})}
        pruefe(f"{name}: Luecken genau an den festen Stellen ({len(soll)})", ist == soll, str(ist ^ soll))
    breit = csv_zeilen("besuche_jahresverlauf")
    leer = {(r["jahr"], r["standort"], m) for r in breit for m in gen.MONATSNAMEN if r[m] == ""}
    pruefe("besuche_jahresverlauf: leer nur Aussenstelle 2024 jun/jul/aug",
           leer == {("2024", "Außenstelle", m) for m in ("jun", "jul", "aug")}, str(leer))
    z = csv_zeilen("benutzung_monatlich")
    pruefe("Platzauslastung auch in Luecken-Monaten vorhanden", all(r["platzauslastung"] != "" for r in z))


def test_eigenschaften():
    print("Gestaltete Eigenschaften:")
    z = csv_zeilen("benutzung_monatlich")

    def summe(st, j, sp):
        return sum(int(r[sp]) for r in z if r["standort"] == st and r["jahr"] == str(j) and r[sp] != "")
    a = [summe("Hauptstelle", j, "ausleihen") for j in gen.STAT_JAHRE]
    b = [summe("Hauptstelle", j, "besuche") for j in gen.STAT_JAHRE]
    pruefe("Hauptstelle: Ausleihen 2025 unter 2022, auch 2024 unter 2022", a[3] < a[0] and a[2] < a[0], str(a))
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
    pruefe("genau die zwei festen leeren Boegen", leer == gen.EVAL_LEERE_BOEGEN, str(leer))
    pruefe("Bewertungen nur 1 bis 5 oder leer", all(r[s] in ("", "1", "2", "3", "4", "5")
                                                    for r in ev for s in ("zufriedenheit", "verstaendlichkeit")))
    pruefe("Weiterempfehlung nur ja, nein oder leer", {r["weiterempfehlung"] for r in ev} <= {"ja", "nein", ""})

    def quote(zg):
        g = [r for r in ev if r["zielgruppe"] == zg]
        return sum(r["weiterempfehlung"] == "" for r in g) / len(g)
    pruefe("Externe lassen die Weiterempfehlung haeufiger offen",
           quote("Externe") > max(quote("Studierende"), quote("Beschäftigte")))
    zuf = [int(r["zufriedenheit"]) for r in ev if r["zufriedenheit"]]
    pruefe("Bewertungen haeufen sich bei 4 und 5", sum(v >= 4 for v in zuf) / len(zuf) > 0.6)


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
        if feld == "k. A.":
            return ""
        if "," in feld:
            return feld.replace(",", ".")
        return feld.replace(".", "")
    gleich = len(daten) == len(sauber) and all(
        d[0] == s["monat"][:7] and d[1] == s["standort"]
        and [zurueck(x) for x in d[2:]] == [s["besuche"], s["ausleihen"], s["fernleihbestellungen"],
                                            s["platzauslastung"]]
        for d, s in zip(daten, sauber))
    pruefe("mit Semikolon, Dezimalkomma, Tausenderpunkt und k. A. gelesen = benutzung_monatlich", gleich)
    pruefe("k. A. genau so oft wie Luecken", roh.count("k. A.") == sum(
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
    pruefe("acht Datenzeilen = besuche_jahresverlauf", len(daten) == 8 and all(
        all(gleicher_wert(v, b[m]) if v is not None else b[m] == "" for v, m in zip(d[2:14], gen.MONATSNAMEN))
        for d, b in zip(daten, breit)))
    pruefe("Summenspalte = Zeilensumme", all(d[14] == sum(v for v in d[2:14] if v is not None) for d in daten))
    summe = w[12]
    pruefe("Summenzeile = Spaltensummen", summe[0] == "Summe" and all(
        summe[2 + i] == sum((d[2 + i] or 0) for d in daten) for i in range(12)))


def test_sollwerte():
    print("Sollwerte:")
    datei = json.loads((WURZEL / "loesungen" / "statistik.golden.json").read_text(encoding="utf-8"))
    neu = json.loads(json.dumps(gen.statistik_sollwerte(SDIR), ensure_ascii=False, sort_keys=True))
    pruefe("statistik.golden.json = Neuberechnung aus den CSV-Dateien", datei == neu)
    fl = [int(r["dauer_tage"]) for r in csv_zeilen("fernleihe_dauer")]
    pruefe("Stichprobe unabhaengig gerechnet: Median und Mittelwert der Fernleihdauer",
           datei["fernleihe_dauer"]["dauer_tage"]["median"] == statistics.median(fl)
           and datei["fernleihe_dauer"]["dauer_tage"]["mittelwert"] == round(statistics.mean(fl), 2))
    readme = (SDIR / "README.md").read_text(encoding="utf-8")
    pruefe("README kennzeichnet die Daten als erfunden", "erfunden" in readme and gen.MARKER in readme)


if __name__ == "__main__":
    for t in [test_reproduzierbar, test_csv_gleich_excel, test_luecken, test_eigenschaften,
              test_fernleihe, test_evaluation, test_export_csv, test_jahresbericht, test_sollwerte]:
        t()
        print()
    fehler = ERGEBNISSE.count(False)
    print(f"{len(ERGEBNISSE)} Pruefungen, {'ALLE BESTANDEN' if not fehler else f'{fehler} FEHLGESCHLAGEN'}")
    sys.exit(1 if fehler else 0)
