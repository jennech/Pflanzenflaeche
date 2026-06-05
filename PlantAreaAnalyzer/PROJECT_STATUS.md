# Project Status

Stand: 2026-06-05

Dieses Dokument fasst den aktuellen Stand von `PlantAreaAnalyzer` zusammen:
was bereits funktioniert, wie das Projekt aufgebaut ist, welche Grenzen noch
sichtbar sind und welche naechsten Schritte sinnvoll sind.

## Kurzfazit

`PlantAreaAnalyzer` ist inzwischen deutlich mehr als ein MVP. Die App kann
Petrischalenbilder laden, anzeigen, zoomen, segmentieren, manuell korrigieren,
Ergebnisse berechnen und als CSV exportieren. Fuer schwierige Bilder gibt es
Presets, einen Auto-Vorschlag, eine gefuehrte Einstellung, Tooltips und
manuelle Nachkorrekturen.

Der groesste offene Punkt ist nicht mehr die reine Bedienbarkeit, sondern die
Robustheit der Segmentierung bei schwierigen Bildtypen:
blasse oder graugruene Blaetter, dunkles Medium, Wurzeln, helle Saeume,
Stoerflecken und stark komprimierte WhatsApp-Bilder koennen sich farblich
ueberlappen. Die App kann das bereits teilweise abfangen, aber sie arbeitet
noch heuristisch und nicht mit einem trainierten Bildmodell.

## Aktueller Funktionsumfang

- Bilder koennen ueber die GUI geladen und analysiert werden.
- Der aktuelle Dateiname wird in der App angezeigt.
- Originalbild und Ergebnisbild werden nebeneinander dargestellt.
- Zoom, Verschieben und Zuruecksetzen der Ansicht sind eingebaut.
- Die Petrischale wird automatisch erkannt und kann eingeblendet werden.
- Die Petrischale kann manuell gesetzt und fein verschoben werden.
- Der Innenradius begrenzt die Analyse auf den inneren Auswertebereich der Schale.
- Gruene Blattbereiche werden ueber HSV, Gruen-Dominanz, Gruen-Index und weitere Nachbearbeitung erkannt.
- Es gibt Presets fuer Standardfaelle, dunkle Blaetter, blasse Blattbasis und strengere Wurzelunterdrueckung.
- Es gibt einen Button `Werte vorschlagen`, der aus Bildmerkmalen und Referenzbeispielen Startwerte ableitet.
- Es gibt eine gefuehrte Einstellung mit Ausschlussfragen fuer typische Probleme.
- Manuelle Stoerflaechen koennen per Klick entfernt werden.
- Blattflaeche kann per Klick mit einem Pinsel manuell ergaenzt werden.
- Manuelle Blatt-Ergaenzungen haben eine Undo-Funktion.
- Die Pinselgroesse wird pro gesetztem Klick gespeichert und soll nicht nachtraeglich alle alten Klicks veraendern.
- Ueberlappende manuelle Pinselklicks zaehlen nur als belegte Maskenflaeche, nicht mehrfach.
- Ergebnisse werden als Kennzahlen angezeigt: gruene Pixel, Petrischalenflaeche, Pflanzenflaeche und Flaechenbedeckung.
- CSV-Export schreibt Ergebnisdaten inklusive Einstellwerten und manueller Korrekturen.
- CSV-Export kann bestehende CSV-Dateien erweitern, statt nur neue Dateien zu erzeugen.
- Die Fenstergeometrie und Splitterpositionen werden gespeichert.
- Das rechte Bedienpanel ist scrollbar und Bereiche wie Ergebnisse/manuelle Korrektur sind einklappbar.
- Beispielbilder und Referenzwerte liegen im Repository und koennen fuer Regressionstests genutzt werden.

## Architektur

### Einstieg

- `main.py` startet die PySide6-Anwendung.
- `start_macos.sh` ist ein macOS-Startskript fuer die lokale Entwicklung.
- `requirements.txt` enthaelt die benoetigten Python-Abhaengigkeiten.

### GUI-Schicht

Die GUI liegt im Ordner `app/`.

- `app/main_window.py`
  - Hauptfenster, Layout, Splitter, Datei-Laden, CSV-Speichern, Reanalyse und GUI-State.
  - Haelt den aktuellen Bildpfad, gecachte Bilddaten, erkannte/manuelle Petrischale und manuelle Korrekturen.
  - Persistiert Fenster- und Splittergroessen mit `QSettings`.

- `app/image_viewer.py`
  - Anzeige von Original- und Ergebnisbild.
  - Zoom, Pan, Doppelklick-Anpassung.
  - Interaktive Klicks fuer Petrischale, Stoerflaechen und manuelle Blatt-Ergaenzungen.

- `app/settings_panel.py`
  - Slider, Presets und Tooltips fuer die Segmentierung.
  - Baut aus der GUI den zentralen `AnalysisSettings`-Datensatz.

- `app/guided_settings_dialog.py`
  - Gefuehrte Fragen fuer haeufige Problemsituationen.
  - Leitet daraus sinnvolle Startwerte ab.

- `app/results_table.py`
  - Darstellung der berechneten Messwerte.

### Analyse-Schicht

Die Bildanalyse liegt im Ordner `analysis/`.

- `analysis/settings.py`
  - Zentrale Dataclasses fuer HSV-Schwellen und Analyseparameter.
  - Enthaelt auch Parameter fuer manuelle Korrekturen.

- `analysis/green_segmentation.py`
  - Hauptpipeline der Segmentierung.
  - Laedt oder nutzt gecachte BGR-Bilder.
  - Skaliert grosse Bilder fuer Performance herunter und rechnet Masken wieder auf Originalgroesse zurueck.
  - Kombiniert HSV-Maske, Gruen-Dominanz, Gruen-Index, Petrischalenmaske, blasse Erweiterung, Morphologie, Flaechenfilter, Wurzeltrim und manuelle Korrekturen.

- `analysis/auto_settings.py`
  - Erstellt automatische Einstellungsvorschlaege.
  - Nutzt Bildsignaturen, Referenzbeispiele und Plausibilitaetspruefungen.
  - Bewertet Kandidaten anhand von Blattkern, Flaeche, Komponenten, Randkontakt, Satelliten und Wurzel-/Medium-Risiko.

- `analysis/petri_detection.py`
  - Automatische Kreiserkennung der Petrischale.

- `analysis/calibration.py`
  - Kalibrierung ueber Petrischalendurchmesser.
  - Aktuell wird standardmaessig von 55 mm Petrischalendurchmesser ausgegangen.

- `analysis/measurement.py`
  - Rechnet aus Maske und Kalibrierung Pixel, mm^2 und Flaechenbedeckung.

- `analysis/overlay.py`
  - Erstellt die Visualisierung der erkannten Pflanzenflaeche.

### Daten, Referenzen und Export

- `data/examples/`
  - Beispielbilder fuer typische Faelle.
  - Diese Bilder sollen im GitHub-Repository bleiben, weil sie fuer Vergleich, Regression und Dokumentation wichtig sind.

- `data/examples/README.md`
  - Beschreibt Zweck der Beispielbilder und wie sie fuer Validierung genutzt werden.

- `data/reference/reference_settings.json`
  - Kuratierte Referenzwerte fuer Beispielbilder.
  - Dient der App als Orientierung fuer aehnliche Bilder, sollte aber nicht als Nutzer-Export missverstanden werden.

- `exports/export_csv.py`
  - CSV-Export fuer Messergebnisse.
  - Schreibt mit UTF-8-Sig, damit Excel unter Windows die Datei gut erkennt.
  - Haengt neue Analysen an bestehende Dateien an.
  - Aktualisiert aeltere CSV-Header automatisch, wenn neue Spalten hinzukommen.

- `exports/export_excel.py`
  - Platzhalter bzw. vorbereiteter Bereich fuer spaeteren Excel-Export.

- `data/models.py`, `data/database.py`, `data/repositories.py`
  - Platzhalter fuer eine spaetere persistente Datenstruktur.

### Tests und Werkzeuge

- `tests/`
  - Unit-Tests fuer Segmentierung, Auto-Einstellungen, Petrischalen-Erkennung, Messung, Kalibrierung, Export und gefuehrte Einstellungen.

- `tools/compare_example_settings.py`
  - Vergleichswerkzeug fuer Beispielbilder und Referenzwerte.

Der letzte bekannte Teststand vor diesem Statusdokument war:

- `42 passed`
- `tools/compare_example_settings.py` erfolgreich gegen die bekannten Beispielbilder
- `git diff --check` ohne Whitespace-Fehler

Dieses Statusdokument selbst ist eine Dokumentationsaenderung; dafuer wurde
keine erneute komplette Testsuite benoetigt.

## Aktueller Entwicklungsstand im Git-Arbeitsbaum

Zum Zeitpunkt dieser Zusammenfassung gibt es uncommitted Aenderungen in:

- `analysis/auto_settings.py`
- `analysis/green_segmentation.py`
- `app/main_window.py`
- `tests/test_auto_settings.py`

Diese Aenderungen gehoeren zum aktuellen Arbeitsstand rund um:

- Performance bei groesseren Bildern durch Downsampling und Caching.
- Verbesserte Auto-Vorschlaege mit Referenzvergleich und Plausibilitaetsscoring.
- Manuelle Korrekturen mit Blatt-Pinsel, Pinselradius und Undo.
- Tests gegen problematische Auto-Segmentierungsfaelle.

Wichtig: Diese Aenderungen sollten nicht versehentlich verworfen werden.

## Bekannte Grenzen

### Segmentierung bleibt schwierig

Die App segmentiert aktuell regelbasiert. Das ist transparent und ohne Training
nutzbar, aber es hat Grenzen:

- Wurzeln, Saeume und Medium koennen farblich nah an blassen Blaettern liegen.
- Graugruene oder schlecht versorgte Blaetter sind fuer Farbschwellen schwer.
- WhatsApp- oder Messenger-komprimierte Bilder verlieren feine Farbinformationen.
- Stark verschiedene Bildtypen brauchen teils unterschiedliche Parameter.
- Manche Bilder benoetigen weiterhin manuelle Blatt-Ergaenzung oder Stoerflaechen-Entfernung.

### Auto-Vorschlaege sind Heuristik, kein Modell

`Werte vorschlagen` versucht gute Startwerte zu finden, aber:

- Es darf nicht nur auf einzelne Dateinamen optimiert werden.
- Neue Bilder sollten anhand von Bildmerkmalen und Aehnlichkeit zu Referenzen behandelt werden.
- Die Referenzwerte in `data/reference/reference_settings.json` sind wertvoll, aber noch klein.
- Die Bewertung muss weiter lernen, wann ein Vorschlag Medium/Wurzeln uebernimmt.

### Kalibrierung ist noch vereinfacht

Aktuell basiert die Flaechenberechnung auf der Petrischale mit Standarddurchmesser
55 mm. Das ist fuer gleiche Schalentypen praktikabel, aber noch nicht ideal.

Offen sind:

- frei einstellbarer Schalen-Durchmesser in der GUI
- Kalibrierung ueber das Karopapier oder bekannte Referenzlaengen
- Speicherung der Kalibrierung pro Messreihe oder Projekt

### Per-Pflanze-Auswertung fehlt noch

Momentan wird die gesamte erkannte Blattflaeche pro Bild/Petrischale gemessen.
Bei vier Pflanzen in einer Schale waere mittelfristig sinnvoll:

- automatische oder manuelle Trennung in 4 Pflanzen
- Einzelwerte pro Pflanze
- Gesamtwert plus Einzelwerte
- Umgang mit ineinander uebergehenden Pflanzen

### Export ist nutzbar, aber Projektstruktur fehlt noch

CSV funktioniert bereits, aber ein professioneller Workflow sollte trennen:

- App-Referenzdaten
- Nutzer-Messergebnisse
- Messreihen/Projekte
- exportierte Overlays und Masken
- Einstellungen je Bild

Das ist in `SPEICHERKONZEPT.md` bereits konzeptionell beschrieben, aber noch
nicht komplett umgesetzt.

## Naechste Schritte

### 1. Referenzbasierte Auto-Vorschlaege stabilisieren

Der wichtigste naechste Schritt ist eine kleine Validierungsbasis mit bekannten
guten Werten:

- Beispielbilder weiter in `data/examples/` halten.
- Gute Einstellungen in `data/reference/reference_settings.json` kuratieren.
- Nicht nach Dateinamen optimieren, sondern nach Bildmerkmalen und Aehnlichkeit.
- `tools/compare_example_settings.py` als Regressionstest ausbauen.
- Bei neuen Vorschlaegen pruefen, ob keine alten Beispielbilder schlechter werden.

Ziel: Auto-Vorschlag soll ein guter Startpunkt sein, nicht perfekt, aber selten
katastrophal.

### 2. Manuelle Korrektur als Sicherheitsnetz verbessern

Gerade bei blassen Problemfaellen ist manuelle Korrektur realistisch und
wissenschaftlich ehrlicher als eine falsche Vollautomatik.

Sinnvolle Verbesserungen:

- Pinselgroesse pro Klick beibehalten.
- Undo fuer einzelne manuelle Klicks weiter absichern.
- Optional kleinere/groessere Pinsel schneller erreichbar machen.
- Eventuell Modus `Blattkante ergaenzen`, der nahe vorhandener Blattmaske bleibt.
- Manuelle Korrekturen im CSV und spaeter im Projektordner nachvollziehbar speichern.

### 3. Speicherstruktur professionalisieren

Empfohlene Struktur:

```text
data/
  examples/             Beispielbilder fuer Entwicklung und Tests
  reference/            kuratierte Referenzwerte fuer App-Logik
exports/                einfache Nutzer-CSV-Exporte
projects/               spaetere Messreihen mit Bildern, Masken, Overlays, JSON
```

Kurzfristig:

- CSV-Export weiterhin in `exports/` empfehlen.
- App soll beim Speichern klarer zwischen neuer Datei und bestehender Datei unterscheiden.
- Button oder Option `An bestehende CSV anhaengen` waere fuer Nutzer eindeutiger als ein reiner Save-Dialog.

Mittelfristig:

- Projektordner pro Messreihe.
- `project.json` mit Metadaten.
- `results.csv` als menschenlesbarer Export.
- `overlays/` und `masks/` fuer Nachvollziehbarkeit.

### 4. README und Anleitung synchronisieren

`ANLEITUNG.md` ist bereits deutlich weiter als der README-Stand. Der README
sollte nachgezogen werden:

- aktueller Funktionsumfang
- Windows-Installation
- CSV-Export und Referenzdaten trennen
- Hinweise zu Bildqualitaet
- typische Bedienstrategie fuer schwierige Bilder

### 5. Kalibrierung erweitern

Naechste sinnvolle Ausbaustufe:

- GUI-Feld fuer Petrischalendurchmesser
- Speicherung dieses Werts im CSV
- optional spaeter Kalibrierung ueber Karopapier

### 6. Windows-Nutzung absichern

Kurzfristig:

- Windows-Anleitung testen.
- `python -m venv .venv` und `.venv\Scripts\activate` dokumentieren.
- Start per `python main.py` sicherstellen.
- CSV-Encoding mit Excel unter Windows pruefen.

Mittelfristig:

- optional `start_windows.bat`
- spaeter PyInstaller-Build, falls Nutzer keine Python-Installation pflegen sollen

## Empfohlene Bedienstrategie fuer schwierige Bilder

1. Bild in moeglichst hoher Originalqualitaet verwenden, nicht aus WhatsApp, wenn vermeidbar.
2. Petrischale pruefen und bei Bedarf manuell korrigieren.
3. `Werte vorschlagen` als Startpunkt nutzen.
4. Wenn es schlecht ist, passendes Preset probieren.
5. Bei blassen Blaettern nicht blind alles erweitern, weil sonst Wurzeln/Saeume mitkommen.
6. Stoerflaechen per Klick entfernen.
7. Fehlende Blattteile mit manuellem Blatt-Pinsel ergaenzen.
8. CSV speichern und Einstellungen fuer spaetere Referenz nachvollziehbar halten.

## Technische Risiken

- Die Segmentierung kann ohne Trainingsdaten keine menschliche Formerkennung voll ersetzen.
- Zu viele Sonderregeln koennen einzelne Bilder verbessern und andere verschlechtern.
- Deshalb sollten Aenderungen immer gegen mehrere Beispielbilder getestet werden.
- Messenger-Kompression kann Farbgrenzen so stark verschlechtern, dass keine robuste Automatik moeglich ist.
- Hohe Bildaufloesung verbessert Informationen, kann aber Auto-Vorschlaege langsamer machen; Downsampling reduziert das bereits.

## Moegliche groessere Ausbaurichtung

Falls die App spaeter wirklich robust und weniger manuell werden soll, gibt es
zwei realistische Pfade:

### Pfad A: Heuristik weiter verbessern

- schneller umzusetzen
- transparent und nachvollziehbar
- gut fuer wenige, kontrollierte Bildtypen
- bleibt bei schwierigen Grenzfaellen manuell

### Pfad B: Annotierte Trainingsdaten und Modell

- benoetigt manuell markierte Masken als Ground Truth
- deutlich robuster bei Form, Blattstruktur und blassen Blaettern
- kann Wurzeln besser lernen, wenn genug Beispiele vorhanden sind
- mehr Aufwand fuer Datenpflege, Training, Versionierung und Validierung

Fuer den aktuellen Stand ist Pfad A sinnvoll. Parallel sollte die App aber so
gebaut werden, dass spaeter Ground-Truth-Masken und ein Modell ergaenzt werden
koennen.

## Wichtigste Dateien

- `main.py` - Startpunkt der App
- `app/main_window.py` - Hauptfenster und Bedienlogik
- `app/settings_panel.py` - Presets, Slider, Tooltips
- `app/image_viewer.py` - Bildanzeige und interaktive Korrekturen
- `analysis/green_segmentation.py` - zentrale Segmentierung
- `analysis/auto_settings.py` - automatische Einstellvorschlaege
- `analysis/settings.py` - Analyseparameter
- `analysis/petri_detection.py` - Petrischalen-Erkennung
- `analysis/calibration.py` - Flaechenkalibrierung
- `analysis/measurement.py` - Kennzahlenberechnung
- `exports/export_csv.py` - CSV-Export
- `data/reference/reference_settings.json` - kuratierte Referenzwerte
- `data/examples/` - Beispielbilder fuer Entwicklung und Tests
- `ANLEITUNG.md` - Bedien- und Installationsanleitung
- `SPEICHERKONZEPT.md` - Konzept fuer Datenhaltung und Export

## Konkreter Vorschlag fuer den naechsten Arbeitsblock

1. Aktuelle Aenderungen mit der Testsuite absichern.
2. `README.md` auf den echten App-Stand bringen.
3. CSV-Speichern in der GUI eindeutiger machen: neue Datei vs. anhaengen.
4. Auto-Vorschlag gegen alle Beispielbilder als festen Vergleichstest ausbauen.
5. Danach entscheiden: mehr Algorithmusarbeit oder zuerst Projekt-/Exportstruktur.

