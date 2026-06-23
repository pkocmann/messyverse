# Fixture-Vertrag: Crossref (Works-API)

Gepinnte, offline gespeicherte Antworten der Crossref-API für die DOI-Anreicherung und die Pagination-Übung. Die Übung läuft deterministisch gegen sie; der Live-Aufruf ist ein offen deklarierter Bonus-Schritt (E14).

## Endpoints

Einzel-DOI (eine Datei pro DOI, `/` im DOI durch `_` ersetzt im Dateinamen):

```
https://api.crossref.org/works/<doi>?mailto=<kontakt>
```

Die 6 DOIs stehen in `../../katalog/dois.txt`.

Werk-Suche mit Pagination (`rows`/`offset`, 3 Seiten):

```
https://api.crossref.org/works?query.bibliographic=<query>&rows=5&offset=<0|5|10>&select=DOI,title,author,container-title,issued,type&mailto=<kontakt>
```

Dateien: `suche_seite-1_offset-0.json`, `suche_seite-2_offset-5.json`, `suche_seite-3_offset-10.json`. Query: „knowledge organization controlled vocabulary".

## Vertrag (Soll-Felder)

Einzel-DOI: Objekt mit `message`. Darunter relevant:

- `title` — Liste, Titel ist `title[0]`
- `author` — Liste von Objekten mit `given` und `family`
- `container-title` — Liste, Zeitschrift/Container ist `[0]`
- `issued.date-parts` — verschachtelte Liste, Jahr ist `date-parts[0][0]`
- `type` — Publikationstyp

Suche: `message.total-results` (Gesamttreffer), `message.items` (die `rows` Treffer dieser Seite).

## Capture

- Erfasst am 2026-06-23 mit `fixtures_fangen.py`. Crossref Polite-Pool via `mailto` (Platzhalter `kurs@example.org`).
- JSON kanonisch reserialisiert für stabile Bytes.

## Pagination-Hinweis

Tag 1 nutzt `rows`/`offset`, nicht den Cursor. Die Gesamttrefferzahl (über 1,9 Mio.) zeigt, warum man blättert statt alles zu laden. Die Übung verbindet die drei Seiten zu einer Ergebnisliste.

## Offline-Loader-Test

```python
import json
m = json.load(open("api-fixtures/crossref/10.1038_sdata.2016.18.json"))["message"]
print(m["title"][0], "—", m["container-title"][0], m["issued"]["date-parts"][0][0])
```

Ergibt `The FAIR Guiding Principles for scientific data management and stewardship — Scientific Data 2016`.
