# Beispielbilder fuer die Segmentierung

Diese Bilder dienen als Validierungsset fuer Presets, Auto-Vorschlaege und die gefuehrte Einstellung.
Zu jedem Bild gibt es eine gleichnamige `.txt`-Datei mit Titel, Problemklasse und Analyseziel.
Die dazu passenden kuratierten Startwerte liegen bewusst getrennt in `../reference/reference_settings.json`.
Eigene Messwerte bitte nicht hier speichern, sondern ueber `CSV speichern` nach `exports/` oder in einen Projektordner exportieren.

Wichtig fuer die Bewertung: Es geht um sichtbare Blattflaeche. Wurzeln, helle Saeume, Medium, Glasrand,
Kalibrierpapier und Stoerflecken sollen nicht als Pflanzenflaeche zaehlen.

## Uebersicht

| Datei | Kurztitel | Hauptproblem |
| --- | --- | --- |
| `klein_starker_kontrast_gruen_zu_medium.jpg` | Kleine Pflanzen, starker Kontrast zum dunklen Medium | eher einfacher Fall, aber kleine Objekte |
| `klein_blass_stoerfleck.jpg` | Kleine blasse Pflanzen mit Stoerfleck | wenig Gruen, zentrale Stoer-/Referenzflaeche |
| `groesser_ineinanderuebergehend_dunkle_blaetter.jpg` | Groessere dunkle Blaetter mit uebergehenden Blattbereichen | dunkle/graugruene Blattbasis und zusammenlaufende Pflanzenteile |
| `blass_dunkel_blattinnere_anders.jpg` | Blasse/dunkle Blaetter mit andersfarbigem Blattinneren | Blattinnenbereiche werden leicht ausgelassen |
| `gross_guter_kontrast_viel_wurzel.jpg` | Gute Blattkontraste, aber viele Wurzelanhaenge | Wurzeln und helle Saeume nicht mitzaehlen |
