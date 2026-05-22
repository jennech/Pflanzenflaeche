# Speicherkonzept

## Ziel

Die Auswertung soll nachvollziehbar, wiederholbar und exportierbar sein. Deshalb sollen nicht nur die Ergebniswerte gespeichert werden, sondern auch die Einstellungen, die Petrischalen-Auswahl und manuelle Korrekturen, mit denen diese Werte entstanden sind.

## Speicherstufen

### 1. Sofort-Export als CSV

Der erste sinnvolle Schritt ist ein einfacher CSV-Export pro ausgewertetem Bild oder pro Messserie.

Eine Zeile entspricht einer Bildauswertung.

Empfohlene Spalten:

```text
scan_id
timestamp
image_path
original_filename
dish_code
petri_diameter_mm
petri_center_x
petri_center_y
petri_radius_px
inner_dish_percent
green_pixels
petri_area_mm2
plant_area_mm2
coverage_percent
h_min
h_max
s_min
s_max
v_min
v_max
min_object_area_px
max_object_area_px
green_dominance_margin
green_index_min
leaf_fill_px
pale_leaf_expansion_px
excluded_component_points
manual_petri_circle
analysis_version
notes
```

Vorteile:

- direkt in Excel, Numbers oder R/Python lesbar
- kein Datenbank-Setup notwendig
- gut fuer schnelle Versuchsauswertung

Nachteil:

- Bilder, Einstellungen und Exporte koennen auseinanderlaufen, wenn man Dateien manuell verschiebt.

### 2. Projektordner mit Metadaten

Fuer saubere Laborarbeit sollte jede Messserie in einem Projektordner liegen.

Struktur:

```text
Projektname/
├── images/
│   └── originalbilder
├── overlays/
│   └── erzeugte Kontrollbilder
├── masks/
│   └── binaere Masken optional
├── results.csv
└── project.json
```

`project.json` speichert projektweite Informationen:

```json
{
  "project_name": "Versuch 2026-05-22",
  "created_at": "2026-05-22T10:30:00",
  "petri_diameter_mm": 55.0,
  "expected_plant_count": 4,
  "analysis_version": "mvp-1",
  "notes": ""
}
```

### 3. SQLite-Datenbank

Wenn mehrere Versuchstage, viele Schalen oder Wiederholungen verglichen werden sollen, ist SQLite sinnvoll.

Tabellen:

```text
experiments
dishes
scans
analysis_settings
manual_corrections
exports
```

Kernidee:

- `experiments`: Versuch, Beschreibung, Startdatum
- `dishes`: Schale, Code, Pflanzenzahl, Medium
- `scans`: Bildauswertung pro Zeitpunkt
- `analysis_settings`: alle Reglerwerte als Snapshot
- `manual_corrections`: manuelle Petrischale und entfernte Stoerflaechen
- `exports`: wann welcher Export erzeugt wurde

Wichtig: Einstellungen werden pro Scan als Snapshot gespeichert, nicht nur global. Sonst kann man spaeter nicht mehr rekonstruieren, warum ein alter Wert entstanden ist.

## Exportformate

### CSV

Standardformat fuer Datenanalyse. Sollte zuerst umgesetzt werden.

### Excel

Komfortformat fuer manuelle Arbeit.

Empfohlene Tabs:

- `Auswertungen`: eine Zeile pro Bild
- `Einstellungen`: verwendete Reglerwerte
- `Projekt`: Projektmetadaten
- `Hinweise`: kurze Erklaerung der Spalten

### Kontrollbilder

Optional sollten pro Scan gespeichert werden:

- Overlay-Bild mit gruener Maske
- reine Maske als PNG

Das ist wichtig fuer Qualitaetskontrolle: Man sieht spaeter sofort, ob ein Messwert plausibel war.

## Empfohlene Umsetzung

### Phase 1

- Button `CSV speichern`
- exportiert aktuelle Auswertung als einzelne CSV-Zeile
- wenn Datei existiert: neue Zeile anhaengen

### Phase 2

- Button `Projektordner speichern`
- kopiert Bild, Overlay und Ergebnisse in einen Ordner
- legt `results.csv` und `project.json` an

### Phase 3

- SQLite-Datenbank
- Serienverwaltung in der App
- Vergleich mehrerer Scans pro Schale

## Offene Fachentscheidung

Aktuell wird die gesamte erkannte Blattflaeche pro Schale gemessen. Da meist 4 getrennte Pflanzen vorhanden sind, koennte spaeter zusaetzlich eine Einzelpflanzen-Auswertung entstehen:

- Komponenten erkennen
- den 4 Pflanzenpositionen zuordnen
- Flaeche pro Pflanze speichern

Das sollte aber erst umgesetzt werden, wenn die Gesamtmasken stabil genug sind.
