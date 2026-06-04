# PlantAreaAnalyzer Bedienungsanleitung

Diese Anleitung ist fuer komplette Neueinsteiger gedacht und erklaert die Installation, Bedienung und den Umgang mit Windows.

## 1. Was die App macht

PlantAreaAnalyzer analysiert Bilder von Petrischalen mit Pflanzen und berechnet:

- wie viele gruene Pixel erkannt wurden
- die Pflanzenflaeche in `mm^2`
- die Flaechenbedeckung in Prozent

Die App zeigt dabei:

- das Originalbild
- ein Overlay mit erkannter Flaeche
- die Petrischale als Kreis
- erkannte Stoerflaechen und manuelle Korrekturen

## 2. Was man braucht

Du brauchst:

- einen Rechner mit Windows 10 oder Windows 11, oder alternativ macOS
- Python 3.13
- eine Internetverbindung fuer den ersten Download der Python-Pakete
- ein Bild einer Petrischale im Unterstuetzten Format, zum Beispiel `jpg`, `jpeg`, `png`, `bmp`, `tif` oder `tiff`

Empfehlung:

- arbeite immer in einem eigenen Projektordner
- benutze pro Projekt eine eigene CSV-Datei

## 3. Installation unter Windows

### 3.1 Python installieren

1. Lade Python von [python.org](https://www.python.org/downloads/windows/) herunter.
2. Waehl die 64-bit Version von Python 3.13.
3. Ganz wichtig: setze beim Installer das Haeckchen bei `Add python.exe to PATH`.
4. Starte die Installation.

Wenn Python schon installiert ist, pruefe in PowerShell:

```powershell
py --version
```

oder:

```powershell
python --version
```

Wenn kein Python gefunden wird, ist es meist nicht im PATH oder noch nicht installiert.

### 3.2 Projekt herunterladen

Am einfachsten ist es, das Projekt von GitHub als ZIP herunterzuladen oder per Git zu klonen.

Wenn du Git benutzt:

```powershell
git clone https://github.com/jennech/Pflanzenflaeche.git
cd Pflanzenflaeche/PlantAreaAnalyzer
```

Wenn du ZIP-Dateien benutzt:

1. ZIP von GitHub herunterladen
2. entpacken
3. in den Ordner `PlantAreaAnalyzer` wechseln

### 3.3 Virtuelle Umgebung anlegen

Die App soll in einer eigenen virtuellen Umgebung laufen. Das verhindert Konflikte mit anderen Python-Projekten.

Im Projektordner:

```powershell
py -3.13 -m venv .venv
```

Falls `py -3.13` nicht geht, probiere:

```powershell
python -m venv .venv
```

### 3.4 Virtuelle Umgebung aktivieren

In PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

In der klassischen Eingabeaufforderung `cmd`:

```bat
.venv\Scripts\activate.bat
```

Falls PowerShell die Aktivierung blockiert, einmalig fuer den Benutzer:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Danach PowerShell neu oeffnen und die Aktivierung nochmals versuchen.

### 3.5 Abhaengigkeiten installieren

Mit aktivierter venv:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Falls `pip` nicht gefunden wird:

```powershell
python -m pip install -r requirements.txt
```

### 3.6 App starten

Im Projektordner:

```powershell
python main.py
```

## 4. Bedienung der App

### 4.1 Bild laden

Klicke auf `Bild laden` und waehle ein Bild aus.

Danach erscheint:

- links das Originalbild
- rechts die Analyseansicht
- rechts unten die Ergebnisse

### 4.2 Zoomen und Verschieben

In den Bildansichten kannst du:

- mit dem Mausrad zoomen
- mit zwei Fingern auf dem Trackpad zoomen
- per Drag das Bild verschieben
- mit Doppelklick wieder anpassen

### 4.3 Petrischale anzeigen

Die Checkbox `Petrischale anzeigen` blendet den orangefarbenen Kreis ein oder aus.

Der blaue gestrichelte Kreis zeigt die innere Analysezone.

### 4.4 Petrischale manuell setzen

Wenn die automatische Erkennung nicht gut sitzt:

1. Hake `Petrischale manuell setzen` an.
2. Klicke zuerst auf den Mittelpunkt der Schale.
3. Klicke dann auf den Rand, um den Radius festzulegen.
4. Falls noetig, nutze die Feinkorrektur:
   - `Hoch`
   - `Runter`
   - `Links`
   - `Rechts`
   - `Radius -`
   - `Radius +`

Wichtig:

- Auf dem Trackpad geht das auch ohne Maus.
- Erst grob klicken, danach fein verschieben.

### 4.5 Stoerflaechen entfernen

Wenn Hintergrund, Label, Wurzeln oder andere falsche Bereiche mit als gruen erkannt werden:

1. Hake `Stoerflaeche per Klick entfernen` an.
2. Klicke auf den stoerenden gruenen Bereich.
3. Die App entfernt die zugehoerige erkannte Flaeche.
4. Mit `Entfernte Flaechen zuruecksetzen` kannst du alles rueckgaengig machen.

### 4.6 Segmentierung einstellen

Die Regler unter `Segmentierung` steuern, wie streng die App gruene Flaechen erkennt.

Bevor du einzelne Regler lange suchst, nutze zuerst:

- `Gefuehrt einstellen`: stellt einfache Fragen wie "dunkles Medium?",
  "Wurzeln/Saeume stoeren?" oder "blasse Blattteile fehlen?" und setzt daraus
  passende Startwerte. Das gleiche findest du oben im Menue `Analyse`.
- `Werte vorschlagen`: probiert mehrere Segmentierungsstrategien und waehlt die plausibelste Maske als Startpunkt.
- Preset `Dunkle Blaetter`: fuer dunkles Medium und wenig leuchtendes Gruen.
- Preset `Dunkle Blaetter + Wurzeln streng`: wenn `Dunkle Blaetter` gut startet, aber noch zu viele Wurzelanhaenge mitnimmt.
- Preset `Blasse Blaetter`: fuer helle oder gelbliche Blattbereiche.
- Preset `Streng gegen Wurzeln`: wenn Wurzeln, helle Saeume oder Medium zu stark erkannt werden.

Danach sollte nur noch Feintuning noetig sein.

Wenn `Werte vorschlagen` genutzt wurde, steht im Preset-Feld `Auto-Vorschlag`.
Wenn du die gefuehrte Auswahl genutzt hast, steht dort `Gefuehrt`.
Sobald du danach einen Regler manuell bewegst, wechselt die Anzeige auf
`Benutzerdefiniert`.

Die wichtigsten Regler:

- `H min` und `H max`: Hue-Farbbereich
- `S min` und `S max`: Farbsaettigung
- `V min` und `V max`: Helligkeit
- `Min Flaeche`: kleine Fehltreffer ignorieren
- `Max Flaeche`: zu grosse Artefakte ignorieren
- `Gruen-Abstand`: gruene Pixel muessen deutlich gruener als rot und blau sein
- `Gruen-Index`: weitere Robustheit fuer schwierige Bilder
- `Blatt-Fuell.`: hilft, kleine Luecken in den Blattbereichen zu schliessen
- `Blass-Erweit.`: erweitert schwach gruene Blattbereiche vorsichtig
- `Innenradius %`: bestimmt, wie weit die Analyse innerhalb der Schale stattfindet

Wenn du einen Regler verschiebst, wird sofort neu analysiert.

Hinweis fuer dunkle Petrischalen: `H min` sehr weit nach oben zu schieben ist oft
keine gute Loesung. Dadurch wird nicht einfach "mehr Blatt" erkannt, sondern der
Bereich verschiebt sich in Richtung blaugruen/cyan. Dort liegen haeufig
Farbsaeume, Wurzelschatten und Randartefakte. Besser zuerst `Werte vorschlagen`
oder `Streng gegen Wurzeln` nutzen und danach nur vorsichtig nachregeln.

## 5. Ergebnisse lesen

Die Ergebnistabelle zeigt:

- `Gruene Pixel`
- `Petrischalenflaeche`
- `Pflanzenflaeche`
- `Flaechenbedeckung`

Das ist die Standardauswertung fuer ein einzelnes Bild.

## 6. CSV speichern

Nach der Analyse kannst du auf `CSV speichern` klicken.

Dann:

1. waehle eine Ergebnisdatei, zum Beispiel `exports/plantarea_results.csv`
2. die App schreibt eine CSV-Datei, wenn sie noch nicht existiert
3. weitere Messungen werden an dieselbe Datei angehaengt

Die CSV enthaelt nicht nur das Ergebnis, sondern auch die verwendeten Einstellungen. Das ist wichtig, damit spaeter nachvollziehbar bleibt, wie ein Wert entstanden ist.

Wichtig: Die Beispiel- und Referenzdaten der App liegen unter `data/examples/` und `data/reference/`.
Dort bitte keine eigenen Ergebnis-CSV-Dateien ablegen. Fuer eigene Messreihen besser `exports/` oder einen eigenen Projektordner verwenden.

## 7. Typische Probleme und Loesungen

### Problem: Python startet nicht

Pruefe:

- ist Python installiert?
- ist `Add python.exe to PATH` gesetzt?
- funktioniert `py --version`?

### Problem: `pip install -r requirements.txt` klappt nicht

Meist hilft:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Problem: PowerShell erlaubt die Aktivierung der venv nicht

Dann einmalig:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Oder stattdessen `cmd` benutzen.

### Problem: Die Petrischale wird falsch erkannt

Dann:

- `Petrischale manuell setzen` aktivieren
- Mittelpunkt und Radius neu setzen
- mit `Hoch`, `Runter`, `Links`, `Rechts`, `Radius -`, `Radius +` fein nachstellen

### Problem: Zu viele Wurzeln oder Fehlstellen werden als gruen erkannt

Dann:

- wenn `Dunkle Blaetter` sonst gut passt: `Dunkle Blaetter + Wurzeln streng` probieren
- sonst Preset `Streng gegen Wurzeln` probieren
- `Min Flaeche` erhoehen
- `Gruen-Abstand` erhoehen
- `Gruen-Index` erhoehen
- `Blatt-Fuell.` vorsichtig anpassen
- `Blass-Erweit.` reduzieren, wenn zu viel Hintergrund aufgenommen wird
- stoerende Bereiche per Klick entfernen

## 8. Wie man am besten mit Windows-Usern arbeitet

Fuer Windows-Anwender ist ein klarer, einfacher Ablauf am besten:

1. Python installieren
2. Projekt herunterladen
3. venv anlegen
4. Abhaengigkeiten installieren
5. `python main.py` starten

Zusatzempfehlung:

- Leg eine kurze `README_WINDOWS.md` oder `ANLEITUNG.md` im Repo an
- Fuege kleine Startskripte wie `start_windows.bat` hinzu
- Verteile spaeter eine ZIP-Datei oder einen GitHub Release fuer den reinen Download

## 9. Macht ein separater Ordner fuer Windows Sinn?

Kurz: eher nein, nicht als eigene Hauptloesung.

Besser ist:

- ein gemeinsames Repo fuer den Quellcode
- eine klare Windows-Anleitung
- optional Startskripte fuer Windows
- fuer Nicht-Entwickler ein GitHub Release als ZIP-Datei

Warum:

- ein separater Ordner im Repo ist fuer Entwickler ok, fuer Anwender aber oft verwirrend
- ein Release ist einfacher herunterzuladen und stabiler zu verteilen
- so bleiben macOS und Windows im selben Projekt, ohne Doppelstruktur

Wenn du willst, kann ich als naechsten Schritt noch eine kleine Windows-Startdatei und eine noch kuerzere Quickstart-Version fuer absolute Anfaenger anlegen.
