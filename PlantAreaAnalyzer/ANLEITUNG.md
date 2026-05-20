# PlantAreaAnalyzer - Anleitung

## Worum es geht

PlantAreaAnalyzer ist eine kleine Desktop-App mit PySide6 und OpenCV, mit der grüne Pflanzenflaechen in Petrischalenbildern analysiert werden koennen.

Aktueller MVP-Stand:

- Bild laden
- Originalbild anzeigen
- Gruene Bereiche im HSV-Farbraum segmentieren
- Overlay oder Maske anzeigen
- Gruene Pixel zaehlen
- Pflanzenflaeche in `mm^2` ausgeben
- Flaechenbedeckung in Prozent ausgeben
- Platzhalter-Kalibrierung fuer eine Petrischale mit `55 mm` Durchmesser

## Was du jetzt machen musst

1. Ein Terminal im Ordner `PlantAreaAnalyzer` oeffnen.
2. Eine virtuelle Umgebung anlegen.
3. Die Abhaengigkeiten installieren.
4. Die App starten.

## Schnellstart

```bash
python3 -m venv .venv313
source .venv313/bin/activate
pip install -r requirements.txt
python main.py
```

Auf diesem Mac sollte die App mit der Homebrew-Python-Umgebung `.venv313` gestartet werden:

```bash
bash start_macos.sh
```

Die alte `.venv` basiert auf Apples Xcode-Python `3.9.6` und kann mit PySide6/Qt auf Apple Silicon abstuerzen.

## Falls du auf macOS arbeitest

Auch wenn die App spaeter fuer Windows gedacht ist, entwickeln wir hier auf macOS. Das ist kein Problem.

Wichtig ist nur:

- `Python 3` muss installiert sein
- `pip` muss funktionieren
- die App laesst sich lokal starten

## Wenn die Installation nicht klappt

Falls `pip install -r requirements.txt` fehlschlaegt, pruefe zuerst:

- Ist die virtuelle Umgebung aktiv?
- Ist eine Internetverbindung vorhanden?
- Blockiert macOS den Zugriff auf den Python-Cache?

Wenn du willst, kann ich dir als naechstes noch eine kleine Startdatei oder ein einfaches Setup-Skript anlegen.
