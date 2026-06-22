# Plan: messyverse — das Übungsuniversum

Status: Entwurf für Review. P0 (Andocken + Kanon) ist umgesetzt; P1/P2 (Befüllung) folgen nach diesem Review.

## 1. Zweck und Scope

Ein öffentliches Repo mit einer kohärenten fiktiven Organisation, das als gemeinsame Zielscheibe für KI-gesteuerte Übungen dient. Erst-Konsument ist python-mit-ki Tag 2. Welt-förmig angelegt, damit `dokumente-ordnen`, die Markdown-Kurse, Excel/Power-Query und der Wissensrepräsentations-Workshop später ihren Ausschnitt dazulegen. Gebaut wird in der ersten Welle nur der Tag-2-Seed. Begründung für eine Welt statt vieler: Glaubwürdigkeit durch Querverweise, eine Pflegestelle statt mehrerer, Wiederverwendung über Kurse hinweg.

## 2. Die Welt

Definiert im Kanon `WELT.md` (Stelle der Wahrheit). Kurz: Bibliothek und Archiv eines fiktiven Instituts, Abteilungen funktional benannt (Einkauf, Verzeichnen, Ablage, Verwaltung), damit der Transfer auf jeden Verwaltungskontext sofort gelingt. Org-Arbeitsname ist „Institut für Verwaltungs- und Regionalkunde" (web-geprüft kollisionsfrei; ersetzt den mit der realen OEAW-Einrichtung kollidierenden Namen „Institut für Stadt- und Regionalforschung / ISR"). PK bestätigt das Setting; jeder erfundene Name läuft durch das Kollisions-Gate (§ Akzeptanzkriterien P1).

## 3. Artefakt-Inventar, auf die Tag-2-Übungen gemappt

| Tag-2-Übung | Welt-Artefakt | Ort |
|---|---|---|
| ISBN → Open Library | reale ISBNs + gecachte Antworten | `katalog/isbns.txt`, `api-fixtures/openlibrary/` |
| DOI → Crossref | reale DOIs + gecachte Antworten | `katalog/dois.txt`, `api-fixtures/crossref/` |
| PDF-Extraktion | erfundene Rechnungen/Bestätigungen (echte PDFs) | `erwerbung/*.pdf` |
| Datei-Umbenennen/Sortieren | Scan-Zoo mit gewachsenen Namen | `magazin/` |
| KI-Verschlagwortung | Titel/Aktenbeschreibungen → kontrolliertes Vokabular | `katalog/`, `katalog/schlagworte.csv` |

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
- Zwei Prüf-Modi (E12): (a) exaktes Soll für ISBN/DOI-Abfrage, PDF-Extraktion und Datei-Sortieren; (b) Constraint-Prüfung für die KI-Verschlagwortung — alle Schlagworte stammen aus dem kontrollierten Vokabular, die Pflicht-Facetten sind besetzt. Ein nicht maschinenprüfbares Soll würde das Versprechen „prüfen gegen das Universum" untergraben.

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

- Org-Name (E3, erledigt): Arbeitsname jetzt „Institut für Verwaltungs- und Regionalkunde" (web-geprüft kollisionsfrei). PK bestätigt/justiert das Setting; ein neuer Name läuft durch das Kollisions-Gate.
- `loesungen/` öffentlich (mit Reveal-Disziplin) oder in separatem privatem Branch/Repo?
- Übungsumfang Tag 2: wie viele der fünf Aufgabentypen kommen wirklich in die 3,5 Stunden?
- Reale ISBN-/DOI-Auswahl für den Katalog (welche Titel).

## Akzeptanzkriterien P1 (Plan-Review 2026-06-22)

Diese Auflagen aus dem Plan-Review sind vor der P1-Befüllung verbindlich. Sie betreffen den Generator und die erzeugten Daten; gebaut wird in einer eigenen Session.

- Namens-Hygiene-Gate (E3): Alle erfundenen Eigennamen — Lieferanten, Sachbearbeiter, der Org-Name — werden vor P1 gegen Handelsregister und Web geprüft. Die Regel steht im Kanon (`WELT.md`, Daten-Hygiene). Erledigt für Quellmann Fachbuch GmbH und das Institut; jeder weitere Name durchläuft den Check.
- Querverweis-Kette (E2): Die Verbindung Rechnung — Katalog — Haushalt — Vermerk läuft über eine eindeutige Schlüsselspalte (Rechnungs-Nummer oder ISBN), identisch auf beiden Seiten; Betrag und Datum sind nur Plausi-Kontrolle (nie auf nicht-eindeutige Attribute joinen). Die Rechnung trägt je Buch eine Positionszeile mit ISBN, Kurztitel und Einzelpreis. Der Generator prüft die Schlüssel-Eindeutigkeit als Assertion. Edge-Cases sitzen an festen Positionen, damit `loesungen/` über Regenerationen stabil bleibt. Umfang: rund 8 bis 10 vollständige Ketten plus 2 bis 3 bewusst unvollständige. Werte und Anatomie sind im Kanon (`WELT.md`) definiert.
- PDF-Scope (E9): Die erste Welle baut Rechnungen und Bestätigungen als PDF. „Digitale Aktenausdrucke" aus der Kursbeschreibung kommen entweder als dritter PDF-Typ in P1 hinzu oder werden bewusst gegen die fixierte Kursbeschreibung als Auslassung dokumentiert — keine stille Lücke.
- Pagination-Fixtures (E9): `api-fixtures/crossref/` enthält ein Werk-Suche-Set mit rows/offset über 2 bis 3 Seiten (Tag 1 nur rows/offset, nicht cursor), damit das Kursversprechen „Web-Abfragen mit Pagination" gedeckt ist — oder die Auslassung wird bewusst dokumentiert. Koppelt an den offen deklarierten Live-Bonus (E14).
- Drift-Schutz für Generator und Output (E6): Generator und erzeugtes Universum werden beide committet, deshalb braucht es einen Schutz gegen stillen Drift zwischen Code und Artefakt. (1) Feste Seed-Zahl fixieren. (2) Marker „GENERIERT — nicht editieren" in erzeugte Dateien und Header. (3) Reproduzieren-Gate: ein Generator-Lauf gefolgt von `git diff --exit-code` muss sauber bleiben. (4) PDF- und xlsx-Timestamps deterministisch setzen, sonst ändern sich die Bytes trotz fixem Seed. (5) Generator-Wartungs- und Regenerations-Doku für Schema-Änderungen.
- schlagworte-Kanonisierung (E8): Das Verschlagwortungs-Mapping zeigt auf `katalog/schlagworte.csv` statt auf einen nicht-kanonischen Ordner `schlagworte/`. Diese CSV ist zugleich das kontrollierte Vokabular (E12). Die Variante bleibt robust, ob die KI-Verschlagwortung in der ersten Welle bleibt oder nicht: das Mapping zeigt in beiden Fällen auf den kanonischen `katalog/`.
- Kontrolliertes Vokabular und Golden-Schema (E12): Das kontrollierte Vokabular `katalog/schlagworte.csv` ist ein P1-/Kanon-Artefakt, falls die KI-Verschlagwortung in der ersten Welle bleibt — sonst wird die Verschlagwortung explizit aus der ersten Tag-2-Welle ausgeklammert (koppelt an den offenen Umfangs-Punkt in §9). Pro Übung wird ein Golden-Output-Schema definiert (Golden CSV/JSON/Markdown bzw. `loesungen/`-Manifest), nicht erst als spätere Ablage — verbindet sich mit dem Verifikations-Layer (E15).

## Lizenz

`LICENSE` liegt im Repo-Root und lizenziert getrennt, weil die drei Bestandteile rechtlich unterschiedlich liegen (E5): Code (`generieren.py`, die Notebooks) unter MIT; synthetische Daten unter CC0 1.0; reale ISBN-/DOI-Fakten und die über Open Library/Crossref bezogenen öffentlichen Metadaten sind nicht mitlizenziert, weil Fakten nicht schutzfähig sind. Ab P1/P2 tragen die einzelnen Dateien SPDX-Header (`MIT` bzw. `CC0-1.0`). Die getrennte Lizenzierung ist der Gesamt-Lizenz vorzuziehen (im Review als CC-BY-SA 4.0 fürs ganze Repo vorgeschlagen): ein einziger Copyleft-Stempel würde realen Fakten einen Schutz anmaßen, den sie nicht haben, und Code-Wiederverwendung unnötig an Share-alike binden.
