"""Regressionstest der SETUP-Zelle in den Uebungs-Notebooks.

Getestet wird die AUSGELIEFERTE Zelle: sie wird aus den .ipynb extrahiert, nicht
aus einer Kopie gelesen. Eine Kopie koennte vom Artefakt wegdriften.

Aufruf aus dem Repo-Wurzelverzeichnis:  python tests/test_setup_zelle.py
"""
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
NBDIR = WURZEL / "notebooks"


def setup_zelle() -> str:
    """Extrahiert die SETUP-Zelle und stellt sicher, dass alle Notebooks dieselbe tragen."""
    varianten = {}
    for nb in sorted(NBDIR.glob("*.ipynb")):
        d = json.loads(nb.read_text())
        treffer = [
            "".join(c["source"])
            for c in d["cells"]
            if c["cell_type"] == "code" and "".join(c["source"]).startswith("# SETUP")
        ]
        assert len(treffer) == 1, f"{nb.name}: {len(treffer)} SETUP-Zellen (erwartet 1)"
        varianten.setdefault(treffer[0], []).append(nb.name)
    assert len(varianten) == 1, (
        f"SETUP-Zellen sind auseinandergelaufen: {[(len(v), v) for v in varianten.values()]}"
    )
    return next(iter(varianten))


def welt(w: Path, gefuellt=True) -> Path:
    for d in ("api-fixtures", "katalog", "notebooks"):
        (w / d).mkdir(parents=True, exist_ok=True)
    if gefuellt:
        (w / "katalog" / "isbns.txt").write_text("x")
        (w / "api-fixtures" / "a.json").write_text("{}")
    return w


def lauf(zelle: str, cwd: Path):
    f = cwd / "_setup_probe.py"
    f.write_text(zelle)
    r = subprocess.run([sys.executable, f.name], cwd=cwd, capture_output=True, text=True)
    f.unlink()
    return r.returncode, r.stdout + r.stderr


def test_lokale_wurzelsuche(zelle: str) -> int:
    fehler = 0
    with tempfile.TemporaryDirectory() as tmp:
        T = Path(tmp)
        a = welt(T / "A" / "Kurs" / "material")
        b = welt(T / "B" / "Kurs" / "material")
        c = welt(T / "C" / "Kurs")
        d = welt(T / "D" / "Kurs")
        (d / "katalog" / "tief").mkdir()
        e = T / "E" / "leer"
        e.mkdir(parents=True)
        f = welt(T / "F" / "Dokumente" / "Kurs" / "messyverse")
        g = T / "G" / "Kurs"
        welt(g / "kopie-a")
        welt(g / "kopie-b")
        h = welt(T / "H" / "Kurs", gefuellt=False)
        i = welt(T / "I" / "ahn")
        (i / "unten" / "tiefer").mkdir(parents=True)

        faelle = [
            ("cwd ist der Notebook-Ordner", a / "notebooks", a.as_posix()),
            ("cwd ist der Kursordner, Welt eine Ebene tiefer", T / "B" / "Kurs", b.as_posix()),
            ("cwd ist die Wurzel selbst", c, c.as_posix()),
            ("cwd steckt tief im Universum", d / "katalog" / "tief", d.as_posix()),
            ("kein Universum in Reichweite", e, "!nicht zu finden"),
            ("Welt zwei Ebenen tiefer", T / "F" / "Dokumente", f.as_posix()),
            ("zwei Arbeitskopien nebeneinander", g, "!mehrere Arbeitskopien"),
            ("Marker vorhanden, aber leer (halber Cloud-Sync)", h, "!nicht zu finden"),
            ("Vorfahr gewinnt nur mangels naeherer Kopie", i / "unten" / "tiefer", i.as_posix()),
        ]
        for name, cwd, erwartet in faelle:
            rc, out = lauf(zelle, cwd)
            if erwartet.startswith("!"):
                ok = rc != 0 and erwartet[1:] in out
            else:
                ok = rc == 0 and erwartet in out.replace("\\", "/")
            print(f"  [{'OK ' if ok else 'FAIL'}] {name}")
            if not ok:
                print("         " + out.strip().replace("\n", "\n         ")[:400])
                fehler += 1
    return fehler


def test_colab_zweig(zelle: str) -> int:
    """Colab: klont nur bei fehlender Kopie -- ein Re-Lauf darf keine Arbeit vernichten."""
    fehler = 0
    for kopie_da in (False, True):
        protokoll = []
        with tempfile.TemporaryDirectory() as tmp:
            content = Path(tmp) / "content"
            content.mkdir()
            ziel = content / "messyverse"
            if kopie_da:
                welt(ziel)
                (ziel / "katalog" / "tn.txt").write_text("Arbeit der Teilnehmerin")
            quelle = zelle.replace('"/content/messyverse"', f'"{ziel}"').replace(
                'Path("/content")', f'Path("{content}")'
            )
            merk = dict(sys.modules)
            sys.modules["google.colab"] = types.ModuleType("google.colab")
            _run, _chdir = subprocess.run, __import__("os").chdir
            subprocess.run = lambda cmd, **kw: (
                protokoll.append(list(cmd)),
                types.SimpleNamespace(returncode=0),
            )[1]
            __import__("os").chdir = lambda p: None
            try:
                exec(compile(quelle, "setup", "exec"), {"__name__": "__main__"})
                ausnahme = None
            except Exception as exc:
                ausnahme = f"{type(exc).__name__}: {exc}"
            finally:
                subprocess.run = _run
                __import__("os").chdir = _chdir
                sys.modules.clear()
                sys.modules.update(merk)

            geklont = any("clone" in p for p in protokoll)
            erhalten = (ziel / "katalog" / "tn.txt").exists() if kopie_da else True
            soll_klonen = not kopie_da
            ok = geklont == soll_klonen and erhalten and not ausnahme
            lage = "ohne vorhandene Kopie" if not kopie_da else "mit vorhandener Kopie"
            print(f"  [{'OK ' if ok else 'FAIL'}] Colab {lage}: "
                  f"klont={geklont} (soll {soll_klonen}), Arbeit erhalten={erhalten}")
            if ausnahme:
                print("         Ausnahme:", ausnahme)
            fehler += 0 if ok else 1
    return fehler


if __name__ == "__main__":
    zelle = setup_zelle()
    print(f"SETUP-Zelle aus {len(list(NBDIR.glob('*.ipynb')))} Notebooks extrahiert, alle identisch.\n")
    print("Lokale Wurzelsuche:")
    fehler = test_lokale_wurzelsuche(zelle)
    print("\nColab-Zweig:")
    fehler += test_colab_zweig(zelle)
    print(f"\n{'ALLE BESTANDEN' if not fehler else f'{fehler} FEHLGESCHLAGEN'}")
    sys.exit(1 if fehler else 0)
