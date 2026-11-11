# WELT.md — Kanon des Übungsuniversums

Dies ist die Stelle der Wahrheit für die fiktive Welt von messyverse. Jeder neue Ausschnitt — ein Datensatz, ein Notebook, eine Aufgabe — prüft sich gegen dieses Dokument. Wer die Welt erweitert, ändert zuerst hier und zieht dann Generator und Dateien nach, nie umgekehrt.

## Die Organisation

Arbeitsname (web-geprüft kollisionsfrei, Setting von PK zu bestätigen): Bibliothek und Archiv des Instituts für Verwaltungs- und Regionalkunde, eine fiktive mittelgroße Spezialeinrichtung. Das Etikett Bibliothek und Archiv ist für das Fachpublikum glaubwürdig; die innere Struktur ist bewusst so benannt, dass jeder Mensch aus Verwaltung, Verein oder Firma sie sofort wiedererkennt. Der Transfer läuft über die Funktion: Einkauf, Verzeichnen, Ablage, Verwaltung gibt es überall.

## Abteilungen — funktional benannt, das ist der Transfer-Hebel

- `erwerbung/` — Einkauf: Lieferantenrechnungen, Bestellbestätigungen (PDF)
- `katalog/` — Verzeichnen: ISBN- und DOI-Listen, Titeldaten, kontrolliertes Schlagwort-Vokabular `schlagworte.csv` (csv/txt)
- `magazin/` — Ablage: digitalisierte Dokumente mit gewachsenen Dateinamen
- `verwaltung/` — Haushalt (xlsx), interne Vermerke; darin `verwaltung/statistik/` — Berichtswesen: Benutzungsstatistik, Evaluation der Schulungen, Fernleihdauer (csv/xlsx), siehe Abschnitt „Berichtswesen“
- `notizen/` — interne Dokumentation (.md)
- `api-fixtures/` — abgelegte Antworten der Web-Kataloge (Open Library, Crossref) für deterministische Übungen

## Daten-Hygiene (hart)

Personenbezogenes ist durchgehend fiktiv: Lieferanten, Sachbearbeiter, Adressen, Aktenzeichen, E-Mail-Adressen. Keine reale Person, keine reale Firmenrechnung — messyverse ist öffentlich.

Erfundene Eigennamen — Lieferanten, Organisationen, Sachbearbeiter, der Org-Name selbst — werden vor der Aufnahme gegen Handelsregister und Web geprüft, damit kein scheinbar fiktiver Name eine reale Firma oder Einrichtung trifft. Der Lieferant Quellmann Fachbuch GmbH und der Org-Name Institut für Verwaltungs- und Regionalkunde sind so geprüft; jeder in P1 ergänzte Name durchläuft denselben Check.

Eine Ausnahme, die kein Widerspruch ist: Im Katalog stehen reale ISBNs und DOIs. Deren öffentliche bibliografische Metadaten sind der Sinn der Open-Library- und Crossref-Übung. Real ist allein die Bibliografie; alles Organisatorische darum herum — wer das Buch wann von wem zu welchem Preis gekauft hat — ist erfunden.

Werte- und Diversitäts-Leitplanke: Die ganze Welt — Katalogtitel, Autorinnen und Autoren, Sachbearbeiter, Vermerke, jede generierte Person und jeder Inhalt — bildet Vielfalt wertschätzend ab: Kulturen, Geschlechter, Epochen und Altersgruppen ausgewogen, ohne Klischee. Tabu sind herabwürdigende Inhalte (etwa homophobe oder rassistische), politischer Extremismus und jede Verherrlichung von Diktaturen, Kriegen oder Verbrechen. Die realen Katalogtitel werden nach denselben Maßstäben kuratiert: klassische, breit katalogisierte Werke aus verschiedenen Kulturkreisen, die freiheitliche Werte vertreten.

## Kern-Entitäten (Seed, in P1 konkretisiert)

- Lieferant: „Quellmann Fachbuch GmbH" (fiktiv); ein bis zwei weitere folgen.
- Haushaltsjahr: 2025 (Datumsrahmen siehe unten).
- Berichtsjahre des Berichtswesens: 2022 bis 2025, fortgeschrieben bis Oktober 2026 (Abschnitt „Berichtswesen“).
- Katalog: rund 10 bis 13 reale, klassische Titel, kuratiert nach der Werte- und Diversitäts-Leitplanke (verschiedene Kulturkreise, Geschlechter, Epochen, Themen); davon ~8 bis 10 mit vollständiger Querverweis-Kette, 2 bis 3 bewusst unvollständig. Die konkreten ISBNs/DOIs werden in P1 live gegen Open Library/Crossref verifiziert, als Fixtures gepinnt (E14) und PK vor dem Generieren zur Freigabe vorgelegt.

## Die Querverweis-Kette — das Glaubwürdigkeits-Rückgrat

Die Welt trägt rund 8 bis 10 vollständige Querverweis-Ketten und 2 bis 3 bewusst unvollständige — eine Rechnung ohne passende Haushaltszeile, ein Katalogeintrag ohne Beleg. Die unvollständigen sind kein Defekt, sondern der Lernanlass für „was fehlt hier?".

Jede Kette läuft über einen eindeutigen Schlüssel durch vier Formate. Der Schlüssel ist die Rechnungs-Nummer oder die ISBN, und er steht identisch auf beiden Seiten jeder Verbindung. Betrag und Datum dienen nur der Plausibilitäts-Gegenkontrolle; auf solche nicht-eindeutigen Attribute wird nie gejoint.

Eine Rechnung in `erwerbung/` (PDF, Lieferant Quellmann Fachbuch GmbH) trägt eine eindeutige Rechnungs-Nummer und je Buch eine Positionszeile mit ISBN, Kurztitel und Einzelpreis. Das Buch mit der ISBN steht im `katalog/`. Die Haushaltszeile in `verwaltung/haushalt.xlsx` führt dieselbe Rechnungs-Nummer als Schlüssel; Betrag und Datum stimmen zusätzlich überein. Ein Vermerk in `notizen/` nennt die Anschaffung unter derselben Rechnungs-Nummer.

Wer in einer Übung die Rechnung ausliest, verbindet über den Schlüssel auf Katalog und Haushalt und prüft das Ergebnis gegen das Universum.

## Datumsrahmen

Erwerbung, Katalog-Belege, Haushalt, Vermerke und Magazin spielen im Haushaltsjahr 2025 (Belege Januar bis Dezember 2025). Das Berichtswesen unter `verwaltung/statistik/` reicht als einziger Teil über 2025 hinaus; sein Rahmen steht im Abschnitt „Berichtswesen“. Die Rohdaten tragen bewusst gemischte Datumsformate (TT.MM.JJJJ, JJJJ-MM-TT, „3. März 2025") — regel-lösbar, der Anlass für eine Vereinheitlichungs-Übung.

## Berichtswesen (`verwaltung/statistik/`)

Die Verwaltung trägt jeden Monat die Benutzungszahlen der Bibliothek zusammen und berichtet sie einmal im Jahr. Dieser Teil der Welt ist der einzige, der mehrere Jahre umfasst, weil Trends, Saisonverläufe und Zeitreihen erst über mehrere Jahre sichtbar werden. Erster Verbraucher ist der WBZ-Kurs „Statistik verstehen und visualisieren“ (Orange, dazu R und Python); die Dateien taugen ebenso für Excel-, Power-Query- und Diagramm-Übungen.

Rahmen: Berichtsjahre 2022 bis 2025 mit Monatswerten Januar bis Dezember, dazu eine Fortschreibung Januar bis Oktober 2026 als „neue Daten“, auf die ein fertiger Auswertungsablauf unverändert angewandt wird. Die Fernleihdauer umfasst die Bestellungen der Außenstelle im Jahr 2025, die Evaluation die Schulungen 2022 bis 2025. Neue Eigennamen gibt es in diesem Teil nicht: Standorte (Hauptstelle, Außenstelle) und Schulungen (Katalogrecherche, Datenbankrecherche, Fernleihe und Dokumentlieferung, Archivführung) tragen Gattungsnamen, Personen kommen nicht vor.

Die Dateien (je CSV und Excel mit gleichem Inhalt, Spaltenbeschreibung in `verwaltung/statistik/README.md`):

- `benutzung_monatlich` — je Monat und Standort Besuche (Eingangszählung), Ausleihen, Fernleihbestellungen und Platzauslastung des Lesesaals in Prozent (aus der Sitzplatzbuchung, also unabhängig vom Zählgerät).
- `benutzung_2026` — dieselben Spalten für Januar bis Oktober 2026.
- `besuche_jahresverlauf` — die Besuche in Breitform, eine Zeile je Jahr und Standort, zwölf Monatsspalten.
- `evaluation_schulungen` — ein Rückmeldebogen je Zeile: Zielgruppe (Studierende, Beschäftigte, Externe), Zufriedenheit und Verständlichkeit von 1 (gar nicht) bis 5 (sehr), Weiterempfehlung ja/nein.
- `fernleihe_dauer` — eine Fernleihbestellung der Außenstelle 2025 je Zeile mit Lieferweg, Medium und Dauer in Tagen. Querverweis: Die Anzahl je Monat entspricht genau `fernleihbestellungen` der Außenstelle in `benutzung_monatlich`.

Gestaltete Eigenschaften, die die Übungen tragen und die Tests absichern: Die Ausleihen sinken über die Jahre, die Besuche steigen; August und Dezember sind die ruhigen Monate, Oktober und November die vollen. Die Fernleihdauer ist rechtsschief, ihr Mittelwert liegt deutlich über dem Median, und drei Buchbestellungen aus dem Ausland brauchen über 90 Tage. Die Bewertungen der Evaluation häufen sich bei 4 und 5.

Feste Lücken, nie verschoben: Besuche der Außenstelle Juni bis August 2024 (Zählgerät defekt) und März 2026 (ebenso), Ausleihen der Hauptstelle November 2023 (Systemumstellung). In der Evaluation fehlen einzelne Antworten, bei Externen häufiger als bei den anderen Gruppen; zwei Bögen (EV-2023-021, EV-2025-037) sind ganz leer abgegeben. Lücken sind leere Zellen, keine Null. Eine Folge ist beabsichtigt: Jahressummen über Lücken fallen zu niedrig aus.

Zwei Dateien sind bewusst unordentlich, als Anlass für sauberes Einlesen: `benutzung_export.csv` ist `benutzung_monatlich` als Systemexport mit zwei Vorspannzeilen, Semikolon, Dezimalkomma, Tausenderpunkt und einem Punkt „.“ für fehlende Werte (eine Markierung, die Orange beim CSV-Import als fehlend erkennt; „k. A.“ erkennt es nicht); `jahresbericht_besuche.xlsx` ist der Jahresverlauf als Berichtstabelle mit Titelzeile, Leerzeile, Summenspalte, Summenzeile und Hinweisblatt. Datumsangaben bleiben auch dort im ISO-Format (JJJJ-MM-TT, im Export JJJJ-MM), weil gängige Werkzeuge deutsche Datumsangaben beim Einlesen still als Monat und Tag vertauschen; ein solcher Fehler wäre für Anfängerinnen und Anfänger nicht zu erkennen.

Kennzeichnung als fiktiv und Lizenz: Die CSV-Dateien und die Sollwert-Datei tragen keinen Kopfkommentar, weil er das Einlesen stören würde (wie bei `katalog/isbns.txt`); Hinweis, Lizenz (`SPDX-License-Identifier: CC0-1.0`) und Generierungsmarker tragen stellvertretend das README des Ordners, das Blatt „Hinweis“ jeder Excel-Datei und die Vorspannzeile des Exports.

Sollwerte und Rechenregeln (`loesungen/statistik.golden.json`): Grundkennwerte sind Anzahl, Summe, Mittelwert, Median, Minimum und Maximum, die Orange, R und Python gleich rechnen; Quartile stehen bewusst nicht darin, weil Werkzeuge sie verschieden rechnen. Jahressummen gibt es nur für Zählgrößen, jeweils mit der Zahl der Monate mit Wert, damit eine Summe über Lücken als unvollständig erkennbar ist; Prozentwerte werden nicht summiert, sondern als ungewichteter Mittelwert der Monatswerte geführt. Abgeleitete Kennzahlen nennen ihre Regel: „Ausleihen je 100 Besuche“ gilt je Monat nur, wenn beide Werte vorhanden sind, und wird je Jahr zweifach verdichtet, als Mittelwert der Monatswerte und als Verhältnis der Summen derselben Monate; der Anteil der Weiterempfehlung bezieht sich auf die beantworteten Bögen. Das Teiljahr 2026 wird nur mit denselben Monaten des Vorjahres verglichen (Januar bis Oktober), nie mit einem ganzen Jahr.

## Datei- und Unordnungs-Konventionen (gemustert, regel-lösbar)

Die Dateinamen im `magazin/` sind gewachsen: `Scan_2025_03_final_FINAL_v2.pdf`, `dokument (3).pdf`, `IMG_0421.pdf`. Sie lassen sich per Regel nach Datum und Vorgang sortieren oder umbenennen. Pro Bereich rund 15 bis 30 Objekte — real genug zum Glauben, wenig genug zum Überblicken.

## Bewusste Edge-Cases — sie zielen auf die Tag-2-Fehlerklassen

Die Kursbeschreibung nennt als Lernziel unter anderem „fehlende Behandlung leerer Einträge, übersehene Sonderfälle". Die Welt enthält daher absichtlich leere Einträge — etwa eine 0-Byte-Datei im `magazin/` —, eine Rechnung ohne Betragszeile, einen Titel mit „z.B." (verfälscht eine naive Satz- oder Tokenzählung) und einen Eintrag mit Umlauten und Sonderzeichen im Namen. Diese Fälle sind kein Defekt, sondern der Lernanlass: KI-generierter Code übersieht sie typischerweise, und genau das soll im Kurs auffallen.

## Änderungs-Disziplin

Die Welt erweitern heißt: zuerst dieses Dokument aktualisieren, dann `generieren.py` und die Dateien nachziehen. Keine Einzeldatei einführen, die hier nicht verzeichnet ist.
