https://github.com/jennech/Pflanzenflaeche.git

## Tech Stack
Sprache: Python
Bildanalyse: OpenCV
GUI: PySide6 / Qt for Python
Datenbank: SQLite
Export: CSV / Excel
Packaging: PyInstaller

## Datenmodell
id
name
description
created_at
updated_at

## Dishes
id
experiment_id
dish_code
diameter_mm
plant_count
medium_description
created_at
updated_at

## Tabelle Scans
id
dish_id
scan_date
day_after_start
image_path
original_filename
pixel_diameter
mm_per_pixel
petri_area_mm2
green_area_mm2
coverage_percent
analysis_status
created_at
updated_at

## Einzelauswertung
id
scan_id
plant_index
region_name
green_area_mm2
coverage_percent_of_dish
bbox_x
bbox_y
bbox_width
bbox_height
created_at

## analysis_settings
id
name
h_min
h_max
s_min
s_max
v_min
v_max
min_object_area_px
morphology_kernel_size
created_at
updated_at

## 6. Bildanalyse-Logik
Schritt 1: Bild laden
Bild mit OpenCV einlesen
Farbraum BGR zu HSV konvertieren
optional Bild verkleinern für Vorschau
Schritt 2: Petrischale erkennen

MVP:

manuelle Kreis-Auswahl durch Nutzer
Nutzer klickt Mittelpunkt und Rand oder zieht Kreis auf

Später:

automatische Kreiserkennung mit Hough Circle Transform
Schritt 3: Kalibrierung
mm_per_pixel = 55.0 / pixel_diameter
pixel_area_mm2 = mm_per_pixel²
Schritt 4: Grünmaske erzeugen

HSV-Schwellenwerte für Grün:

h_min
h_max
s_min
s_max
v_min
v_max

Die App soll diese Werte einstellbar machen.

Schritt 5: Maske bereinigen
kleine Störungen entfernen
Löcher schliessen
Objekte unter Mindestgrösse ignorieren

OpenCV-Funktionen:

cv2.inRange()
cv2.morphologyEx()
cv2.findContours()
Schritt 6: Fläche berechnen
green_pixels = Anzahl weisser Pixel in Grünmaske innerhalb der Petrischale
green_area_mm2 = green_pixels × pixel_area_mm2
coverage_percent = green_area_mm2 / petri_area_mm2 × 100

## Ordnerstruktur
PlantAreaAnalyzer/
│
├── README.md
├── requirements.txt
├── .gitignore
├── main.py
│
├── app/
│   ├── __init__.py
│   ├── main_window.py
│   ├── image_viewer.py
│   ├── settings_panel.py
│   └── results_table.py
│
├── analysis/
│   ├── __init__.py
│   ├── petri_detection.py
│   ├── green_segmentation.py
│   ├── calibration.py
│   ├── measurement.py
│   └── overlay.py
│
├── data/
│   ├── database.py
│   ├── models.py
│   └── repositories.py
│
├── exports/
│   └── export_excel.py
│
├── tests/
│   ├── test_calibration.py
│   └── test_measurement.py
│
└── sample_images/

## requirements.txt
opencv-python
numpy
pandas
openpyxl
PySide6
SQLAlchemy
pytest
pyinstaller

# PlantAreaAnalyzer – Windows-App zur Flächenanalyse von Pflanzen in Petrischalen

## 1. Ziel

Windows-Desktop-App zur Analyse von eingescannten Aufsichtsbildern von Petrischalen.

Die App soll grüne Pflanzenfläche vom braunen Medium unterscheiden und daraus den Flächenbedeckungsgrad berechnen.

Standardfall:

- Petrischale: 55 mm Durchmesser
- 4 Pflanzen pro Schale
- Bildquelle: Scanner / Aufsichtbild
- Pflanze: grün
- Medium: braun
- Wurzeln: weisslich / leicht grünlich, sollen möglichst nicht als Pflanzenfläche zählen

---

## 2. Kernfunktion

Berechnung:

```text
Petrischalenfläche = π × (55 mm / 2)²
Petrischalenfläche ≈ 2375.8 mm²

Flächenbedeckung [%] = erkannte grüne Pflanzenfläche / Petrischalenfläche × 100

