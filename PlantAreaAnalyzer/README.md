# PlantAreaAnalyzer

PlantAreaAnalyzer ist eine Desktop-App zur Analyse gruener Pflanzenflaechen auf
Petrischalenbildern.

Die App kann:

- Bilder laden und anzeigen
- die Petrischale automatisch erkennen oder manuell setzen
- gruene Flaechen segmentieren
- schwierige Bilder mit Presets, Auto-Vorschlag und gefuehrter Einstellung
  unterstuetzen
- manuelle Korrekturen fuer Stoerflaechen und Blattbereiche aufnehmen
- Ergebnisse als CSV exportieren

## Wenn du die App benutzen willst

Der einfachste Einstieg ist:

1. [INSTALLATION_WINDOWS.md](INSTALLATION_WINDOWS.md) lesen
2. Python installieren
3. optional Git installieren, nur wenn du spaeter mit `git pull` updaten willst
4. die App starten

Git ist nicht noetig, wenn du nur eine ZIP-Datei herunterladen und die App
lokal starten willst.

Unter Windows kann die App nach der Einrichtung auch mit
[`start_windows.bat`](start_windows.bat) gestartet werden.

## Bedienung

Die Bedienung der App steht in [ANLEITUNG.md](ANLEITUNG.md).

## Daten und Exporte

- `data/examples/` enthaelt Beispielbilder fuer Entwicklung und Tests
- `data/reference/reference_settings.json` enthaelt kuratierte Referenzwerte
  fuer `Werte vorschlagen`
- `exports/` ist fuer eigene CSV-Ergebnisse gedacht

Eigene Messergebnisse gehoeren nicht in `data/reference/`.

## Technischer Hinweis

Die Kalibrierung verwendet aktuell einen festen Petrischalen-Durchmesser von
55 mm als Standard. Das reicht fuer den aktuellen Entwicklungsstand, kann aber
spaeter erweitert werden.
