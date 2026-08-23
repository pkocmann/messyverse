"""Prueft, ob dieser Rechner fuer den Kurs bereit ist.

Aufruf: in Visual Studio Code diese Datei oeffnen und auf den Start-Pfeil klicken.
Oder im Terminal:  python3 pruefen.py   (Windows:  python pruefen.py)

Das Skript aendert nichts. Es sagt nur, was da ist und was fehlt.
"""

import importlib.util
import sys
from pathlib import Path

# Pakete, die im Kurs gebraucht werden. Der Kommentar erklaert wofuer.
PAKETE = {
    "pandas": "Tabellen",
    "requests": "Abrufe aus Web-Katalogen",
    "pypdf": "Text aus PDF-Rechnungen",
}

# Ordner, an denen wir das Uebungsuniversum erkennen, mit einer Datei zur Stichprobe.
UNIVERSUM = {
    "katalog": "isbns.txt",
    "api-fixtures": None,
    "erwerbung": None,
    "magazin": None,
    "notebooks": None,
}

MINDEST_PYTHON = (3, 9)


def zeile(zustand: str, text: str) -> None:
    print(f"  {zustand:9s} {text}")


def pruefe_python() -> bool:
    v = sys.version_info
    ok = (v.major, v.minor) >= MINDEST_PYTHON
    zeile("in Ordnung" if ok else "zu alt",
          f"Python {v.major}.{v.minor}.{v.micro}"
          + ("" if ok else f" -- gebraucht wird mindestens {MINDEST_PYTHON[0]}.{MINDEST_PYTHON[1]}"))
    return ok


def pruefe_pakete() -> list:
    fehlend = []
    for name, wofuer in PAKETE.items():
        da = importlib.util.find_spec(name) is not None
        zeile("da" if da else "fehlt", f"{name} ({wofuer})")
        if not da:
            fehlend.append(name)
    return fehlend


def pruefe_universum(start: Path) -> bool:
    """Sucht das Uebungsuniversum nach derselben Regel wie die SETUP-Zelle: Naehe schlaegt Ferne."""
    def passt(p: Path) -> bool:
        try:
            return all((p / d).is_dir() and any((p / d).iterdir()) for d in UNIVERSUM)
        except OSError:
            return False

    wurzel = None
    if passt(start):
        wurzel = start
    else:
        for muster in ("*", "*/*"):
            treffer = [p for p in start.glob(muster) if p.is_dir() and passt(p)]
            if treffer:
                wurzel = sorted(treffer)[0]
                break
        else:
            wurzel = next((p for p in list(start.parents)[:6] if passt(p)), None)

    if wurzel is None:
        zeile("fehlt", "Das Uebungsmaterial ist von hier aus nicht zu finden")
        print()
        print(f"  Gesucht wurde ab: {start}")
        print("  Erwartet werden die Ordner " + ", ".join(UNIVERSUM) + ".")
        print("  Entpacken Sie das Kursmaterial in Ihren Kursordner und oeffnen Sie")
        print("  diesen Ordner in Visual Studio Code ueber 'Datei > Ordner oeffnen'.")
        return False

    anzahl = sum(1 for p in wurzel.rglob("*") if p.is_file() and ".git" not in p.parts)
    zeile("da", f"Uebungsmaterial: {anzahl} Dateien unter {wurzel}")
    for ordner, stichprobe in UNIVERSUM.items():
        if stichprobe and not (wurzel / ordner / stichprobe).is_file():
            zeile("unvollstaendig", f"{ordner}/{stichprobe} fehlt -- Entpacken ggf. wiederholen")
            return False
    return True


def main() -> int:
    print()
    print("Kurs 'Python mit KI' -- Bereitschaftspruefung")
    print("=" * 46)
    print()

    print("Python")
    python_ok = pruefe_python()
    print()

    print("Zusatzpakete")
    fehlend = pruefe_pakete()
    print()

    print("Kursmaterial")
    material_ok = pruefe_universum(Path.cwd())
    print()

    print("=" * 46)
    if python_ok and not fehlend and material_ok:
        print("Alles bereit. Sie koennen im Ordner 'notebooks' loslegen.")
        return 0

    print("Noch zu erledigen:")
    if not python_ok:
        print("  - Eine neuere Python-Version installieren (python.org).")
    if fehlend:
        befehl = f"{Path(sys.executable).name} -m pip install " + " ".join(fehlend)
        print("  - Diese Zeile ins Terminal kopieren und ausfuehren:")
        print()
        print(f"      {befehl}")
        print()
    if not material_ok:
        print("  - Das Kursmaterial entpacken, siehe Hinweis oben.")
    print()
    print("Wenn etwas nicht klappt: Der Kurs laeuft auch vollstaendig im Browser.")
    print("Den Link dazu bekommen Sie von der Kursleitung.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
