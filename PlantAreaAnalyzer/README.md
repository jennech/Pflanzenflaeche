# PlantAreaAnalyzer

PlantAreaAnalyzer ist ein modular aufgebautes Python-Projekt fuer die Analyse gruener Pflanzenflaechen auf Bildern von Petrischalen.

Der erste MVP enthaelt:

- eine Desktop-App mit PySide6
- Bildimport
- Gruensegmentierung mit OpenCV im HSV-Farbraum
- Anzeige von Originalbild und Overlay
- Berechnung von Gruenflaeche in mm^2
- Berechnung der Flaechenbedeckung in Prozent
- eine einfache Platzhalter-Kalibrierung mit festem Petrischalen-Durchmesser von 55 mm

Eine detaillierte Bedienungs- und Windows-Anleitung findest du in [ANLEITUNG.md](ANLEITUNG.md).

## Projektstruktur

```text
PlantAreaAnalyzer/
├── README.md
├── requirements.txt
├── main.py
├── app/
├── analysis/
├── data/
├── exports/
└── tests/
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Starten

```bash
python main.py
```

## Hinweis zum MVP

Die Kalibrierung verwendet aktuell noch keinen echten erkannten Kreis. Als Platzhalter wird angenommen, dass die Petrischale ungefaehr die kleinere Bildkante ausfuellt. Damit koennen wir die komplette Pipeline bereits testen und spaeter sauber erweitern.
