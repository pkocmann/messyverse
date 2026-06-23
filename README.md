# messyverse

Ein Übungsuniversum für KI-gestützte Datenaufgaben. messyverse enthält die Dateien einer fiktiven Organisation — eine Bibliothek mit Archiv —, an denen sich kleine, alltagsnahe Automatisierungsaufgaben üben lassen: Metadaten aus Web-Katalogen abrufen, Beträge aus Rechnungen auslesen, unaufgeräumte Dateisammlungen sortieren, Titel verschlagworten.

Die Idee: eine Welt, viele Brillen. Dieselbe Organisation dient als gemeinsame Zielscheibe für unterschiedliche Kurse und Aufgabentypen. Die Strukturen tragen ein Bibliotheks-Etikett, sind aber funktional so benannt, dass sie sich auf jeden Verwaltungskontext übertragen lassen.

## Arbeitsweise

Die Aufgaben werden nicht von Hand programmiert. Man schaut sich die Lage an, formuliert einen Auftrag an einen KI-Assistenten, liest und prüft den erzeugten Code und steuert bei Bedarf nach. Geprüft wird gegen das Universum: zu jeder Aufgabe gibt es ein erwartetes Ergebnis.

## Die Übungen

Jedes Notebook öffnet mit einem Klick in Google Colab. Es lädt die Daten direkt aus diesem Repo (eine bereitgestellte Setup-Zelle legt eine Arbeitskopie an), arbeitet gegen gespeicherte Web-Antworten in `api-fixtures/` (deterministisch) und enthält eine Selbst-Prüfung gegen das erwartete Ergebnis.

| Übung | Worum es geht | Notebook |
|---|---|---|
| ISBN → Open Library | Buchmetadaten zu einer ISBN-Liste abrufen | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pkocmann/messyverse/blob/main/notebooks/01_isbn-open-library.ipynb) |
| DOI → Crossref | Zitationen anreichern + Pagination | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pkocmann/messyverse/blob/main/notebooks/02_doi-crossref.ipynb) |
| PDF-Extraktion | Beträge aus Rechnungen auslesen | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pkocmann/messyverse/blob/main/notebooks/03_pdf-extraktion.ipynb) |
| Datei-Sortieren | Den Scan-Zoo nach Datum ordnen | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pkocmann/messyverse/blob/main/notebooks/04_datei-sortieren.ipynb) |
| KI-Verschlagwortung | Titel ins kontrollierte Vokabular einordnen | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pkocmann/messyverse/blob/main/notebooks/05_ki-verschlagwortung.ipynb) |

Die Daten erzeugt `generieren.py` reproduzierbar aus den gepinnten Fixtures; die Welt-Definition steht in `WELT.md`, der Aufbauplan in `PLAN.md`.
