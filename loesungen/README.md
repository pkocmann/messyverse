<!-- GENERIERT -- nicht editieren (Quelle: generieren.py). Aenderungen gehen beim naechsten Lauf verloren. -->

# loesungen/ -- Verifikations-Layer

Dieser Ordner ist öffentlich und dient dem Selbst-Check im Notebook. Die Sollwerte stehen im Klartext, weil sie ohnehin aus der öffentlichen Welt herleitbar sind: die Lookup-Ergebnisse aus den Fixtures, die Rechnungsbeträge aus den PDFs -- und auch das Soll-Datum beim Datei-Sortieren steht im Datei-Inhalt (Zeile 'Datum:'). Für das Datei-Sortieren liegt deshalb das vollständige Klartext-Mapping Dateiname -> Datum in datei_sortieren.golden.json; der zusätzliche integritaets_sha256 ist nur ein Sekundär-Check gegen versehentliche Veränderung, keine Verschleierung des Solls.
