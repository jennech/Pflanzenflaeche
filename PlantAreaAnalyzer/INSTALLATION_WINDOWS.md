# PlantAreaAnalyzer unter Windows installieren und updaten

Diese Anleitung ist fuer Menschen gedacht, die die App einfach nutzen wollen
und nicht selbst programmieren. Sie zeigt dir den Weg unter Windows 10 und
Windows 11 Schritt fuer Schritt.

Wichtig gleich am Anfang:

- Git ist nicht notwendig, um die App zu benutzen
- Git brauchst du nur, wenn du spaeter bequem mit `git pull` updaten willst
- wenn du Git nicht willst, kannst du einfach ein ZIP herunterladen
- in beiden Faellen brauchst du Python und eine eigene virtuelle Umgebung

## Was du brauchst

- Windows 10 oder Windows 11
- Python 3.13 x64
- Internetverbindung fuer die erste Installation
- ein Bild von einer Petrischale, zum Beispiel `jpg`, `jpeg`, `png`, `bmp`,
  `tif` oder `tiff`
- optional, aber empfohlen: Git

## Weg 1: Ohne Git, am einfachsten fuer absolute Anfaenger

Wenn du die App nur benutzen willst, nimm diesen Weg.

### 1. Python installieren

1. Lade Python von [python.org](https://www.python.org/downloads/windows/) herunter.
2. Nimm die 64-bit Version von Python 3.13.
3. Aktiviere im Installer unbedingt `Add python.exe to PATH`.
4. Schliesse die Installation ab.

Pruefen kannst du die Installation mit:

```powershell
py --version
```

Falls das nicht geht, probiere:

```powershell
python --version
```

### 2. ZIP-Datei herunterladen

1. Oeffne das GitHub-Repo im Browser.
2. Klicke auf `Code`.
3. Lade das Projekt als ZIP herunter.
4. Entpacke die ZIP-Datei in einen Ordner, den du leicht wiederfindest.
5. Oeffne den entpackten Ordner `PlantAreaAnalyzer`.

### 3. Virtuelle Umgebung anlegen

Im Ordner `PlantAreaAnalyzer`:

```powershell
py -3.13 -m venv .venv
```

Falls `py -3.13` nicht gefunden wird:

```powershell
python -m venv .venv
```

### 4. Virtuelle Umgebung aktivieren

In PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

In `cmd`:

```bat
.venv\Scripts\activate.bat
```

Wenn PowerShell das Aktivieren blockiert, einmalig fuer deinen Benutzer:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Danach PowerShell schliessen und neu oeffnen.

### 5. Abhaengigkeiten installieren

Mit aktivierter virtueller Umgebung:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 6. App starten

Im gleichen Ordner:

```powershell
python main.py
```

Oder per Doppelklick auf `start_windows.bat`, wenn die virtuelle Umgebung schon
eingerichtet ist.

## Weg 2: Mit Git, wenn du spaeter einfach updaten willst

Dieser Weg ist fuer Nutzer praktisch, die spaeter nicht jedes Mal eine neue ZIP
herunterladen wollen.

### 1. Python installieren

1. Lade Python von [python.org](https://www.python.org/downloads/windows/) herunter.
2. Nimm die 64-bit Version von Python 3.13.
3. Aktiviere im Installer unbedingt `Add python.exe to PATH`.
4. Schliesse die Installation ab.

Pruefen kannst du die Installation mit:

```powershell
py --version
```

Falls das nicht geht, probiere:

```powershell
python --version
```

### 2. Git installieren

Git ist das Programm, mit dem du spaeter Updates mit `git pull` holen kannst.
Wenn du es noch nicht installiert hast:

1. Lade Git von [git-scm.com](https://git-scm.com/download/win) herunter.
2. Starte die Installation.
3. Die Standard-Einstellungen sind fuer den Anfang in Ordnung.
4. Wenn die Installation fertig ist, kannst du Git im Terminal testen mit:

```powershell
git --version
```

Danach im gewuenschten Ordner das Projekt klonen:

```powershell
git clone https://github.com/jennech/Pflanzenflaeche.git
cd Pflanzenflaeche/PlantAreaAnalyzer
```

### 3. Virtuelle Umgebung anlegen

Im Ordner `PlantAreaAnalyzer`:

```powershell
py -3.13 -m venv .venv
```

Falls `py -3.13` nicht gefunden wird:

```powershell
python -m venv .venv
```

### 4. Virtuelle Umgebung aktivieren

In PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

In `cmd`:

```bat
.venv\Scripts\activate.bat
```

Wenn PowerShell das Aktivieren blockiert, einmalig fuer deinen Benutzer:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Danach PowerShell schliessen und neu oeffnen.

### 5. Abhaengigkeiten installieren

Mit aktivierter virtueller Umgebung:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 6. App starten

Im gleichen Ordner:

```powershell
python main.py
```

Oder per Doppelklick auf `start_windows.bat`, wenn die virtuelle Umgebung schon
eingerichtet ist.

## So laufen spaetere Updates

Wenn du das Projekt mit Git geklont hast, ist ein Update sehr einfach:

1. App schliessen
2. in den Ordner `PlantAreaAnalyzer` wechseln
3. virtuelle Umgebung aktivieren
4. neue Version holen
5. Abhaengigkeiten bei Bedarf neu installieren
6. App starten oder `start_windows.bat` doppelklicken

Die genauen Befehle sind:

```powershell
cd Pflanzenflaeche/PlantAreaAnalyzer
.venv\Scripts\Activate.ps1
git pull
python -m pip install -r requirements.txt
python main.py
```

Wichtig:

- `git pull` bringt nur den neuen Code
- `pip install -r requirements.txt` stellt sicher, dass neue Pakete mit
  installiert werden
- deine eigenen CSV-Dateien und Projektordner solltest du getrennt sichern

Wenn du Ergebnisse in `exports/` speicherst, sichere diesen Ordner vor groesseren
Updates am besten mit.

## Wenn du kein Git benutzen willst

Dann kannst du die App auch als ZIP herunterladen:

1. ZIP-Datei von GitHub herunterladen
2. entpacken
3. Schritte fuer Python, venv und `pip install` wie oben ausfuehren

Updates sind bei dieser Variante etwas haendischer:

1. neue ZIP-Datei herunterladen
2. in einen neuen Ordner entpacken
3. eigene CSV-Dateien und Projektordner aus der alten Installation uebernehmen
4. wieder `python -m pip install -r requirements.txt` ausfuehren

Diese Variante funktioniert, ist aber fuer spaetere Updates weniger bequem als
Git.

## Wenn etwas nicht klappt

### Python wird nicht gefunden

- pruefe, ob Python installiert ist
- pruefe, ob `Add python.exe to PATH` gesetzt war
- teste `py --version`

### PowerShell blockiert die venv

- fuehre `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` aus
- oeffne PowerShell danach neu
- oder nutze stattdessen `cmd`

### `pip install -r requirements.txt` bricht ab

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Die App startet nicht

- stelle sicher, dass die virtuelle Umgebung aktiviert ist
- starte die App mit `python main.py`
- pruefe, ob du im Ordner `PlantAreaAnalyzer` bist

## Empfehlung fuer nicht geuebte Nutzer

Wenn du die App jemandem geben willst, der sich mit Python nicht auskennt,
ist dieser Weg am einfachsten:

1. Python installieren
2. entweder ZIP herunterladen oder Git installieren
3. die Schritte aus `Weg 1` befolgen
4. falls Git benutzt wurde, spaeter mit `git pull` updaten

Damit bleibt die Installation sauber und Updates sind deutlich einfacher als
bei einer ZIP-Loesung.
