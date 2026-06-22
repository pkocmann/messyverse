# WELT.md — Kanon des Übungsuniversums

Dies ist die Stelle der Wahrheit für die fiktive Welt von messyverse. Jeder neue Ausschnitt — ein Datensatz, ein Notebook, eine Aufgabe — prüft sich gegen dieses Dokument. Wer die Welt erweitert, ändert zuerst hier und zieht dann Generator und Dateien nach, nie umgekehrt.

## Die Organisation

Arbeitsname (web-geprüft kollisionsfrei, Setting von PK zu bestätigen): Bibliothek und Archiv des Instituts für Verwaltungs- und Regionalkunde, eine fiktive mittelgroße Spezialeinrichtung. Das Etikett Bibliothek und Archiv ist für das Fachpublikum glaubwürdig; die innere Struktur ist bewusst so benannt, dass jeder Mensch aus Verwaltung, Verein oder Firma sie sofort wiedererkennt. Der Transfer läuft über die Funktion: Einkauf, Verzeichnen, Ablage, Verwaltung gibt es überall.

## Abteilungen — funktional benannt, das ist der Transfer-Hebel

- `erwerbung/` — Einkauf: Lieferantenrechnungen, Bestellbestätigungen (PDF)
- `katalog/` — Verzeichnen: ISBN- und DOI-Listen, Titeldaten (csv/txt)
- `magazin/` — Ablage: digitalisierte Dokumente mit gewachsenen Dateinamen
- `verwaltung/` — Haushalt (xlsx), interne Vermerke
- `notizen/` — interne Dokumentation (.md)
- `api-fixtures/` — abgelegte Antworten der Web-Kataloge (Open Library, Crossref) für deterministische Übungen

## Daten-Hygiene (hart)

Personenbezogenes ist durchgehend fiktiv: Lieferanten, Sachbearbeiter, Adressen, Aktenzeichen, E-Mail-Adressen. Keine reale Person, keine reale Firmenrechnung — messyverse ist öffentlich.

Erfundene Eigennamen — Lieferanten, Organisationen, Sachbearbeiter, der Org-Name selbst — werden vor der Aufnahme gegen Handelsregister und Web geprüft, damit kein scheinbar fiktiver Name eine reale Firma oder Einrichtung trifft. Der Lieferant Quellmann Fachbuch GmbH und der Org-Name Institut für Verwaltungs- und Regionalkunde sind so geprüft; jeder in P1 ergänzte Name durchläuft denselben Check.

Eine Ausnahme, die kein Widerspruch ist: Im Katalog stehen reale ISBNs und DOIs. Deren öffentliche bibliografische Metadaten sind der Sinn der Open-Library- und Crossref-Übung. Real ist allein die Bibliografie; alles Organisatorische darum herum — wer das Buch wann von wem zu welchem Preis gekauft hat — ist erfunden.

## Kern-Entitäten (Seed, in P1 konkretisiert)

- Lieferant: „Quellmann Fachbuch GmbH" (fiktiv); ein bis zwei weitere folgen.
- Haushaltsjahr: 2025 (Datumsrahmen siehe unten).
- Katalog: eine Handvoll realer Titel; die konkreten ISBNs werden in P1 ausgewählt und mit gecachten Open-Library-Antworten in `api-fixtures/` verankert.

## Die Querverweis-Kette — das Glaubwürdigkeits-Rückgrat

Die Welt trägt rund 8 bis 10 vollständige Querverweis-Ketten und 2 bis 3 bewusst unvollständige — eine Rechnung ohne passende Haushaltszeile, ein Katalogeintrag ohne Beleg. Die unvollständigen sind kein Defekt, sondern der Lernanlass für „was fehlt hier?".

Jede Kette läuft über einen eindeutigen Schlüssel durch vier Formate. Der Schlüssel ist die Rechnungs-Nummer oder die ISBN, und er steht identisch auf beiden Seiten jeder Verbindung. Betrag und Datum dienen nur der Plausibilitäts-Gegenkontrolle; auf solche nicht-eindeutigen Attribute wird nie gejoint.

Eine Rechnung in `erwerbung/` (PDF, Lieferant Quellmann Fachbuch GmbH) trägt eine eindeutige Rechnungs-Nummer und je Buch eine Positionszeile mit ISBN, Kurztitel und Einzelpreis. Das Buch mit der ISBN steht im `katalog/`. Die Haushaltszeile in `verwaltung/haushalt.xlsx` führt dieselbe Rechnungs-Nummer als Schlüssel; Betrag und Datum stimmen zusätzlich überein. Ein Vermerk in `notizen/` nennt die Anschaffung unter derselben Rechnungs-Nummer.

Wer in einer Übung die Rechnung ausliest, verbindet über den Schlüssel auf Katalog und Haushalt und prüft das Ergebnis gegen das Universum.

## Datumsrahmen

Alle Vorgänge spielen im Haushaltsjahr 2025 (Belege Januar bis Dezember 2025). Die Rohdaten tragen bewusst gemischte Datumsformate (TT.MM.JJJJ, JJJJ-MM-TT, „3. März 2025") — regel-lösbar, der Anlass für eine Vereinheitlichungs-Übung.

## Datei- und Unordnungs-Konventionen (gemustert, regel-lösbar)

Die Dateinamen im `magazin/` sind gewachsen: `Scan_2025_03_final_FINAL_v2.pdf`, `dokument (3).pdf`, `IMG_0421.pdf`. Sie lassen sich per Regel nach Datum und Vorgang sortieren oder umbenennen. Pro Bereich rund 15 bis 30 Objekte — real genug zum Glauben, wenig genug zum Überblicken.

## Bewusste Edge-Cases — sie zielen auf die Tag-2-Fehlerklassen

Die Kursbeschreibung nennt als Lernziel unter anderem „fehlende Behandlung leerer Einträge, übersehene Sonderfälle". Die Welt enthält daher absichtlich eine leere Datei (0 Byte) im `magazin/`, eine Rechnung ohne Betragszeile, einen Titel mit „z.B." (verfälscht eine naive Satz- oder Tokenzählung) und einen Eintrag mit Umlauten und Sonderzeichen im Namen. Diese Fälle sind kein Defekt, sondern der Lernanlass: KI-generierter Code übersieht sie typischerweise, und genau das soll im Kurs auffallen.

## Änderungs-Disziplin

Die Welt erweitern heißt: zuerst dieses Dokument aktualisieren, dann `generieren.py` und die Dateien nachziehen. Keine Einzeldatei einführen, die hier nicht verzeichnet ist.
