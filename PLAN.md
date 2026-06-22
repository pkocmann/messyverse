# Plan: messyverse — das Übungsuniversum

Status: Entwurf für Review. P0 (Andocken + Kanon) ist umgesetzt; P1/P2 (Befüllung) folgen nach diesem Review.

## 1. Zweck und Scope

Ein öffentliches Repo mit einer kohärenten fiktiven Organisation, das als gemeinsame Zielscheibe für KI-gesteuerte Übungen dient. Erst-Konsument ist python-mit-ki Tag 2. Welt-förmig angelegt, damit `dokumente-ordnen`, die Markdown-Kurse, Excel/Power-Query und der Wissensrepräsentations-Workshop später ihren Ausschnitt dazulegen. Gebaut wird in der ersten Welle nur der Tag-2-Seed. Begründung für eine Welt statt vieler: Glaubwürdigkeit durch Querverweise, eine Pflegestelle statt mehrerer, Wiederverwendung über Kurse hinweg.

## 2. Die Welt

Definiert im Kanon `WELT.md` (Stelle der Wahrheit). Kurz: Bibliothek und Archiv eines fiktiven Instituts, Abteilungen funktional benannt (Einkauf, Verzeichnen, Ablage, Verwaltung), damit der Transfer auf jeden Verwaltungskontext sofort gelingt. Org-Name ist im Review zu bestätigen.

## 3. Artefakt-Inventar, auf die Tag-2-Übungen gemappt

| Tag-2-Übung | Welt-Artefakt | Ort |
|---|---|---|
| ISBN → Open Library | reale ISBNs + gecachte Antworten | `katalog/isbns.txt`, `api-fixtures/openlibrary/` |
| DOI → Crossref | reale DOIs + gecachte Antworten | `katalog/dois.txt`, `api-fixtures/crossref/` |
| PDF-Extraktion | erfundene Rechnungen/Bestätigungen (echte PDFs) | `erwerbung/*.pdf` |
| Datei-Umbenennen/Sortieren | Scan-Zoo mit gewachsenen Namen | `magazin/` |
| KI-Verschlagwortung | Titel/Aktenbeschreibungen → kontrolliertes Vokabular | `katalog/`, `schlagworte/` (später) |

## 4. Daten-Design

- Generator statt Handarbeit: ein seed-fester `generieren.py` (gemeinsame uv-venv: python-docx, reportlab/fpdf, openpyxl) erzeugt das Universum reproduzierbar. Generator und erzeugtes Universum werden beide committet — Teilnehmende klonen fertige Dateien, der Generator hält alles regenerier- und tunbar. Echte PDFs/xlsx, keine Platzhalter.
- Klein: rund 15 bis 30 Objekte pro Bereich.
- Gemusterte, regel-lösbare Unordnung (uneinheitliche Datumsformate, `FINAL_v2`-Namen), kein Zufallschaos.
- Bewusste Edge-Cases, die auf die Tag-2-Fehlerklassen zielen (leere Einträge, Sonderfälle): leere Datei, Rechnung ohne Betrag, Titel mit „z.B.". Details im Kanon.
- Synthetische Personendaten durchgehend; reale ISBNs/DOIs nur im Katalog (öffentliche Bibliografie, Sinn der API-Übung).

## 5. Zugriff und Methode

- Open-in-Colab-Badge pro Übungs-Notebook plus Daten per Raw-URL (kein Klonen als gelehrtes Konzept).
- Für Datei-Baum-Aufgaben eine bereitgestellte idempotente Setup-Zelle als Black Box (vor dem Klonen `rm -rf`, dann clone, „jetzt hast du deine Arbeitskopie").
- Fixtures-first für alles mit API: Übung läuft deterministisch gegen `api-fixtures/`, die Live-Abfrage ist die Kür.
- Steuern statt schreiben: Lage anschauen, KI prompten, Code lesen und prüfen, bei Fehler re-prompten statt von Hand fixen. Pro Übung ein erwartetes Ergebnis in der Lösungs-Ablage, damit das Prüfen gegen das Universum objektiv ist.

## 6. Repo-Struktur

```
messyverse/
  README.md            # TN-facing: was ist das, wie nutze ich es
  WELT.md              # Kanon / Stelle der Wahrheit
  PLAN.md              # dieser Plan
  generieren.py        # seed-fester Generator (P1)
  erwerbung/ katalog/ magazin/ verwaltung/ notizen/   # die Welt (P1)
  api-fixtures/        # gecachte Open-Library-/Crossref-Antworten (P1)
  notebooks/           # Übungs-Notebooks mit Open-in-Colab-Badges (P2)
  loesungen/           # erwartete Ergebnisse (P2; Trennung siehe offene Frage)
```

Lokal, gitignored (nie ins öffentliche Repo): `.mcp.json`, `.vscode/`, `.claude/`, `.github/`, `reindex.sh`, `rules.yaml` — die briefer-/Authoring-Infrastruktur.

## 7. Andocken (P0, umgesetzt)

Slug `messyverse`: MCP-Server `briefer-messyverse` (`.mcp.json`, `--reviewer claude`) und `briefer-gpt-messyverse` (`.vscode/mcp.json`, `--reviewer gpt`), `reindex.sh`-Delegator, `rules.yaml` (leer), Copilot-Instructions-Symlink, Registry-Eintrag. Alle Infrastruktur gitignored, weil das Repo öffentlich ist. Offen: `.claude/settings.json` (SessionStart-Hook + Permissions) braucht deine ausdrückliche Freigabe.

## 8. Bau-Phasen

- P0 (umgesetzt): Andocken + Kanon `WELT.md`.
- P1 (nach Review): Generator + Tag-2-Seed-Daten (Katalog, Fixtures, Rechnungssatz, Magazin-Zoo, `haushalt.xlsx`, die Querverweis-Kette).
- P2 (nach Review): Übungs-Notebooks + erwartete Ergebnisse.
- P3 (später): Ausschnitte für die anderen Kurse.

## 9. Offene Punkte fürs Review

- Org-Name und Setting bestätigen (Arbeitsname ISR).
- `loesungen/` öffentlich (mit Reveal-Disziplin) oder in separatem privatem Branch/Repo?
- Übungsumfang Tag 2: wie viele der fünf Aufgabentypen kommen wirklich in die 3,5 Stunden?
- Reale ISBN-/DOI-Auswahl für den Katalog (welche Titel).

## Lizenz

`LICENSE` liegt im Repo-Root und lizenziert getrennt, weil die drei Bestandteile rechtlich unterschiedlich liegen (E5): Code (`generieren.py`, die Notebooks) unter MIT; synthetische Daten unter CC0 1.0; reale ISBN-/DOI-Fakten und die über Open Library/Crossref bezogenen öffentlichen Metadaten sind nicht mitlizenziert, weil Fakten nicht schutzfähig sind. Ab P1/P2 tragen die einzelnen Dateien SPDX-Header (`MIT` bzw. `CC0-1.0`). Die getrennte Lizenzierung ist der Gesamt-Lizenz vorzuziehen (im Review als CC-BY-SA 4.0 fürs ganze Repo vorgeschlagen): ein einziger Copyleft-Stempel würde realen Fakten einen Schutz anmaßen, den sie nicht haben, und Code-Wiederverwendung unnötig an Share-alike binden.
