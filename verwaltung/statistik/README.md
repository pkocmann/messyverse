<!-- GENERIERT -- nicht editieren (Quelle: generieren.py). Aenderungen gehen beim naechsten Lauf verloren. -->

# verwaltung/statistik/ -- Berichtswesen der Bibliothek

Fiktive Übungsdaten des messyverse (Bibliothek und Archiv des Instituts für Verwaltungs- und Regionalkunde, Berichtswesen). Alle Werte sind erfunden. Lizenz CC0 1.0.

Das Berichtswesen sammelt die Zahlen, die die Verwaltung jeden Monat zusammenträgt und einmal im Jahr berichtet. Die Dateien liegen als CSV (UTF-8, Komma, Punkt als Dezimalzeichen, Datum als JJJJ-MM-TT) und als Excel-Datei mit demselben Inhalt vor; die Excel-Fassung trägt den Hinweis auf fiktive Daten auf dem zweiten Blatt „Hinweis“. Leere Zellen sind fehlende Werte. Kanon und Begründung: WELT.md, Abschnitt „Berichtswesen“; Sollwerte: loesungen/statistik.golden.json.

| Datei | Inhalt |
|---|---|
| `benutzung_monatlich` | Januar 2022 bis Dezember 2025, je Monat und Standort (Hauptstelle, Außenstelle): `besuche` (Eingangszählung), `ausleihen`, `fernleihbestellungen`, `platzauslastung` (Lesesaal, Prozent aus der Sitzplatzbuchung) |
| `benutzung_2026` | dieselben Spalten für Januar bis Oktober 2026 |
| `besuche_jahresverlauf` | die Besuche aus `benutzung_monatlich` in Breitform: eine Zeile je Jahr und Standort, Spalten `jan` bis `dez` |
| `evaluation_schulungen` | Rückmeldebögen zu vier Schulungen 2022 bis 2025: `zielgruppe`, `zufriedenheit` und `verstaendlichkeit` von 1 (gar nicht) bis 5 (sehr), `weiterempfehlung` ja/nein; unbeantwortete Fragen bleiben leer |
| `fernleihe_dauer` | alle Fernleihbestellungen der Außenstelle 2025 mit `lieferweg`, `medium` und `dauer_tage` (Tage bis zur Bereitstellung); die Anzahl je Monat entspricht `fernleihbestellungen` der Außenstelle |
| `benutzung_export.csv` | `benutzung_monatlich` als unordentlicher Systemexport: zwei Vorspannzeilen, Semikolon, Dezimalkomma, Tausenderpunkt, „k. A.“ für fehlende Werte |
| `jahresbericht_besuche.xlsx` | `besuche_jahresverlauf` als Berichtstabelle: Titelzeile, Leerzeile, Summenspalte, Summenzeile, Hinweisblatt |

Bekannte Lücken (feste Positionen): Besuche der Außenstelle Juni bis August 2024 und März 2026 (Zählgerät defekt), Ausleihen der Hauptstelle November 2023 (Systemumstellung).
