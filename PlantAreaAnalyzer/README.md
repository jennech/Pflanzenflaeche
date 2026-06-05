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

Fuer die Installation unter Windows und spaetere Updates findest du die
Schritt-fuer-Schritt-Anleitung in
[INSTALLATION_WINDOWS.md](INSTALLATION_WINDOWS.md).
Die Bedienung der App ist in [ANLEITUNG.md](ANLEITUNG.md) beschrieben.

## Projektstruktur

```text
PlantAreaAnalyzer/
├── README.md
├── requirements.txt
├── main.py
├── app/
├── analysis/
├── data/
│   ├── examples/
│   └── reference/
├── exports/
└── tests/
```

`data/reference/reference_settings.json` enthaelt kuratierte App-Referenzen fuer `Werte vorschlagen`.
Eigene Messergebnisse werden als CSV in `exports/` oder in einem eigenen Projektordner gespeichert und nicht in `data/reference/`.
Unter Windows kann die App nach der Einrichtung auch mit
[`start_windows.bat`](/Users/jenskuehne/Documents/Coding/Coding/Kojla/Pflanzenflaeche/PlantAreaAnalyzer/start_windows.bat)
gestartet werden.

## Starten

Nach der Installation kann die App mit `python main.py` gestartet werden.

## Hinweis zum MVP

Die Kalibrierung verwendet aktuell noch keinen echten erkannten Kreis. Als Platzhalter wird angenommen, dass die Petrischale ungefaehr die kleinere Bildkante ausfuellt. Damit koennen wir die komplette Pipeline bereits testen und spaeter sauber erweitern.
