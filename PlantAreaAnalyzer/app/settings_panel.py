from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from analysis.settings import AnalysisSettings
from analysis.settings import HSVThresholds


SLIDER_HELP: dict[str, str] = {
    "h_min": (
        "Untere Farbton-Grenze fuer Gruen im HSV-Farbraum. Hoeher = gelbe/braune "
        "Bereiche werden eher ausgeschlossen, aber gelbliche Blaetter koennen fehlen."
    ),
    "h_max": (
        "Obere Farbton-Grenze fuer Gruen im HSV-Farbraum. Niedriger = blaue Farbsaeume "
        "und Fremdfarben werden eher ausgeschlossen, aber blaeuliches/dunkles Gruen "
        "kann fehlen."
    ),
    "s_min": (
        "Minimale Farbsattigung. Hoeher = graue/weisse Wurzeln, Reflexe und blasse "
        "Flecken werden weniger erkannt. Zu hoch kann blasse Blaetter verlieren."
    ),
    "s_max": (
        "Maximale Farbsattigung. Meist bei 255 lassen. Nur senken, wenn sehr satte "
        "Farbartefakte oder Markierungen faelschlich erkannt werden."
    ),
    "v_min": (
        "Minimale Helligkeit. Hoeher = sehr dunkle Artefakte werden ausgeblendet. "
        "Zu hoch kann dunkle Blaetter verlieren."
    ),
    "v_max": (
        "Maximale Helligkeit. Niedriger = helle Reflexe/helle Wurzeln werden weniger "
        "erkannt. Zu niedrig kann helle Blaetter abschneiden."
    ),
    "min_object_area_px": (
        "Kleine erkannte Flaechen unterhalb dieser Pixelzahl werden entfernt. Hoeher = "
        "weniger Rauschen/Wurzelreste, aber kleine Blaetter koennen verschwinden."
    ),
    "max_object_area_px": (
        "Sehr grosse zusammenhaengende Maskenflaechen oberhalb dieser Pixelzahl werden "
        "entfernt. Hilft gegen Farbsaeume oder Medium-Artefakte, die zu gross fuer eine "
        "einzelne Blatt-/Pflanzeninsel sind."
    ),
    "green_dominance_margin": (
        "Wie stark der Gruenkanal gegenueber Rot und Blau dominieren muss. Hoeher = "
        "strengere Blatt-Erkennung und weniger Farbsaeume; zu hoch verliert dunkle oder "
        "gelbliche Blaetter."
    ),
    "green_index_min": (
        "Schwelle fuer den Gruen-Index, zusaetzlich zu HSV. Hoeher = weniger false "
        "positives; niedriger = erkennt schwaches/dunkles Gruen besser, kann aber "
        "Wurzeln oder Medium mitnehmen."
    ),
    "leaf_fill_px": (
        "Schliesst kleine Loecher innerhalb bereits erkannter Blattflaechen. Erweitert "
        "nicht grossflaechig; gut fuer gesprenkelte Masken. Zu hoch kann nahe Bereiche "
        "verbinden."
    ),
    "pale_leaf_expansion_px": (
        "Ergaenzt blasse/gelbliche Blattteile nur in der Naehe sicher erkannter gruener "
        "Pixel. Hoeher = mehr helle Blattteile, aber auch mehr Risiko fuer Wurzeln."
    ),
    "inner_dish_percent": (
        "Radius des wirklich ausgewerteten Innenbereichs. Niedriger = Rand, Glas, "
        "Schatten und Farbsaeume werden ausgeschlossen. Der blaue gestrichelte Kreis "
        "zeigt diesen Analysebereich."
    ),
}


class SettingsPanel(QGroupBox):
    settings_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__("Segmentierung")
        self._sliders: dict[str, QSlider] = {}
        self._value_labels: dict[str, QLabel] = {}

        info_label = QLabel(
            "Feinjustierung fuer schwierige Bilder mit Farbsauemen oder schwachem Kontrast."
        )
        info_label.setWordWrap(True)

        slider_grid = QGridLayout()
        self._add_slider(slider_grid, "H min", "h_min", 0, 179, 38, 0)
        self._add_slider(slider_grid, "H max", "h_max", 0, 179, 92, 1)
        self._add_slider(slider_grid, "S min", "s_min", 0, 255, 55, 2)
        self._add_slider(slider_grid, "S max", "s_max", 0, 255, 255, 3)
        self._add_slider(slider_grid, "V min", "v_min", 0, 255, 35, 4)
        self._add_slider(slider_grid, "V max", "v_max", 0, 255, 255, 5)
        self._add_slider(slider_grid, "Min Flaeche", "min_object_area_px", 0, 2500, 120, 6)
        self._add_slider(slider_grid, "Max Flaeche", "max_object_area_px", 0, 120000, 50000, 7)
        self._add_slider(slider_grid, "Gruen-Abstand", "green_dominance_margin", 0, 80, 12, 8)
        self._add_slider(slider_grid, "Gruen-Index", "green_index_min", -30, 80, 8, 9)
        self._add_slider(slider_grid, "Blatt-Fuell.", "leaf_fill_px", 0, 16, 2, 10)
        self._add_slider(slider_grid, "Blass-Erweit.", "pale_leaf_expansion_px", 0, 45, 12, 11)
        self._add_slider(slider_grid, "Innenradius %", "inner_dish_percent", 75, 100, 90, 12)

        reset_button = QPushButton("Standardwerte")
        reset_button.setToolTip(
            "Setzt alle Segmentierungsregler auf die empfohlenen Startwerte zurueck."
        )
        reset_button.clicked.connect(self.reset_defaults)

        layout = QVBoxLayout()
        layout.addWidget(info_label)
        layout.addLayout(slider_grid)
        layout.addWidget(reset_button)
        self.setLayout(layout)

    def analysis_settings(
        self,
        manual_petri_circle: tuple[int, int, int] | None = None,
        excluded_component_points: tuple[tuple[int, int], ...] = (),
    ) -> AnalysisSettings:
        return AnalysisSettings(
            thresholds=self.thresholds(),
            min_object_area_px=self._value("min_object_area_px"),
            max_object_area_px=self._value("max_object_area_px"),
            green_dominance_margin=self._value("green_dominance_margin"),
            green_index_min=self._value("green_index_min"),
            leaf_fill_px=self._value("leaf_fill_px"),
            pale_leaf_expansion_px=self._value("pale_leaf_expansion_px"),
            inner_dish_factor=self._value("inner_dish_percent") / 100.0,
            manual_petri_circle=manual_petri_circle,
            excluded_component_points=excluded_component_points,
        )

    def inner_dish_factor(self) -> float:
        return self._value("inner_dish_percent") / 100.0

    def thresholds(self) -> HSVThresholds:
        return HSVThresholds(
            h_min=self._value("h_min"),
            h_max=self._value("h_max"),
            s_min=self._value("s_min"),
            s_max=self._value("s_max"),
            v_min=self._value("v_min"),
            v_max=self._value("v_max"),
        )

    def reset_defaults(self) -> None:
        defaults = HSVThresholds()
        for name, value in {
            "h_min": defaults.h_min,
            "h_max": defaults.h_max,
            "s_min": defaults.s_min,
            "s_max": defaults.s_max,
            "v_min": defaults.v_min,
            "v_max": defaults.v_max,
            "min_object_area_px": 120,
            "max_object_area_px": 50000,
            "green_dominance_margin": 12,
            "green_index_min": 8,
            "leaf_fill_px": 2,
            "pale_leaf_expansion_px": 12,
            "inner_dish_percent": 90,
        }.items():
            self._sliders[name].setValue(value)
        self.settings_changed.emit(self.analysis_settings())

    def _add_slider(
        self,
        layout: QGridLayout,
        title: str,
        name: str,
        minimum: int,
        maximum: int,
        value: int,
        row: int,
    ) -> None:
        title_label = QLabel(title)
        tooltip = SLIDER_HELP.get(name, "")
        if tooltip:
            title_label.setToolTip(tooltip)

        value_label = QLabel(str(value))
        value_label.setMinimumWidth(32)
        value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if tooltip:
            value_label.setToolTip(tooltip)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
        if tooltip:
            slider.setToolTip(tooltip)
        slider.valueChanged.connect(
            lambda new_value, key=name: self._slider_changed(key, new_value)
        )

        self._sliders[name] = slider
        self._value_labels[name] = value_label

        layout.addWidget(title_label, row, 0)
        layout.addWidget(slider, row, 1)
        layout.addWidget(value_label, row, 2)

    def _slider_changed(self, name: str, value: int) -> None:
        self._value_labels[name].setText(str(value))
        self._keep_min_max_valid(name)
        self.settings_changed.emit(self.analysis_settings())

    def _keep_min_max_valid(self, changed_name: str) -> None:
        pairs = [("h_min", "h_max"), ("s_min", "s_max"), ("v_min", "v_max")]
        for min_name, max_name in pairs:
            min_slider = self._sliders[min_name]
            max_slider = self._sliders[max_name]
            if min_slider.value() <= max_slider.value():
                continue

            if changed_name == min_name:
                max_slider.setValue(min_slider.value())
            else:
                min_slider.setValue(max_slider.value())

    def _value(self, name: str) -> int:
        return self._sliders[name].value()
