# Fixture-Vertrag: Open Library (Books-API)

Diese JSON-Dateien sind gepinnte, offline gespeicherte Antworten der Open-Library-Books-API. Die Übung läuft deterministisch gegen sie; der Live-Aufruf ist ein offen deklarierter Bonus-Schritt (E14).

## Endpoint

```
https://openlibrary.org/api/books?bibkeys=ISBN:<isbn13>&jscmd=data&format=json
```

Eine Datei pro ISBN: `<isbn13>.json`. Die 13 ISBNs stehen in `../../katalog/isbns.txt`.

## Vertrag (Soll-Felder)

Jede Antwort ist ein Objekt mit dem Schlüssel `ISBN:<isbn13>`. Darunter relevant für die Übung:

- `title` — Titel der Ausgabe (Zeichenkette)
- `authors` — Liste von Objekten mit `name`
- `publish_date` — Erscheinungsangabe als Zeichenkette (bewusst uneinheitlich, z.B. `"December 31, 1998"` oder `"2005"` — eine echte Datenrealität)

Hinweis zur Datenqualität: Open Library ist eine offene Datenbank. Manche Ausgaben tragen Übersetzer in der Autorenliste, der Autorname einer arabischen Ausgabe steht in arabischer Schrift, Print-on-Demand-Ausgaben nennen Selbstverlage. Das ist kein Fehler der Fixture, sondern der Lernanlass „Daten sind nicht immer sauber".

## Capture

- Erfasst am 2026-06-23 mit `fixtures_fangen.py` (lokales Werkzeug, nicht Teil des öffentlichen Repos).
- JSON kanonisch reserialisiert (`sort_keys`, `indent=2`, echte Zeichen) für stabile Bytes.

## Offline-Loader-Test

Eine Fixture lädt sich ohne Netz so:

```python
import json
isbn = "9783518111383"
rec = json.load(open(f"api-fixtures/openlibrary/{isbn}.json"))[f"ISBN:{isbn}"]
print(rec["title"], "—", ", ".join(a["name"] for a in rec["authors"]))
```

Ergibt `Okonkwo oder Das Alte stürzt — Chinua Achebe`.
