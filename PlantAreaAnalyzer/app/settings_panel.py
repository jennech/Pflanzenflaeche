from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QSlider,
    QVBoxLayout,
)

from analysis.settings import AnalysisSettings
from analysis.settings import HSVThresholds

AUTO_PRESET_LABEL = "Auto-Vorschlag"
GUIDED_PRESET_LABEL = "Gefuehrt"
CUSTOM_PRESET_LABEL = "Benutzerdefiniert"

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
    "root_trim_px": (
        "Schneidet duenne wurzelartige Anhaenge nach der Farberkennung ab. Hoeher = "
        "mehr Wurzelreste weg; zu hoch kann Blattzipfel oder kleine Blattteile kuerzen."
    ),
    "inner_dish_percent": (
        "Radius des wirklich ausgewerteten Innenbereichs. Niedriger = Rand, Glas, "
        "Schatten und Farbsaeume werden ausgeschlossen. Der blaue gestrichelte Kreis "
        "zeigt diesen Analysebereich."
    ),
}

PRESETS: dict[str, AnalysisSettings] = {
    "Standard": AnalysisSettings(),
    "Dunkle Blaetter": AnalysisSettings(
        thresholds=HSVThresholds(h_min=30, h_max=120, s_min=150, s_max=255, v_min=20),
        min_object_area_px=250,
        max_object_area_px=75000,
        green_dominance_margin=16,
        green_index_min=70,
        leaf_fill_px=3,
        pale_leaf_expansion_px=26,
        inner_dish_factor=0.88,
    ),
    "Dunkle Blaetter + Wurzeln streng": AnalysisSettings(
        thresholds=HSVThresholds(h_min=30, h_max=120, s_min=150, s_max=255, v_min=25),
        min_object_area_px=300,
        max_object_area_px=50000,
        green_dominance_margin=10,
        green_index_min=80,
        leaf_fill_px=0,
        pale_leaf_expansion_px=18,
        root_trim_px=10,
        inner_dish_factor=0.86,
    ),
    "Blasse Blaetter": AnalysisSettings(
        thresholds=HSVThresholds(h_min=25, h_max=115, s_min=25, s_max=255, v_min=35),
        min_object_area_px=180,
        max_object_area_px=45000,
        green_dominance_margin=8,
        green_index_min=0,
        leaf_fill_px=4,
        pale_leaf_expansion_px=16,
        root_trim_px=3,
        inner_dish_factor=0.86,
    ),
    "Blasse Blattbasis + Wurzeln streng": AnalysisSettings(
        thresholds=HSVThresholds(h_min=22, h_max=125, s_min=38, s_max=255, v_min=20),
        min_object_area_px=160,
        max_object_area_px=70000,
        green_dominance_margin=0,
        green_index_min=-5,
        leaf_fill_px=1,
        pale_leaf_expansion_px=32,
        root_trim_px=8,
        inner_dish_factor=0.86,
    ),
    "Streng gegen Wurzeln": AnalysisSettings(
        thresholds=HSVThresholds(h_min=30, h_max=120, s_min=150, s_max=255, v_min=25),
        min_object_area_px=300,
        max_object_area_px=35000,
        green_dominance_margin=10,
        green_index_min=80,
        leaf_fill_px=0,
        pale_leaf_expansion_px=18,
        root_trim_px=10,
        inner_dish_factor=0.86,
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
        self._add_slider(slider_grid, "Wurzel-Trim", "root_trim_px", 0, 10, 4, 12)
        self._add_slider(slider_grid, "Innenradius %", "inner_dish_percent", 75, 100, 90, 13)

        reset_button = QPushButton("Standardwerte")
        reset_button.setToolTip(
            "Setzt alle Segmentierungsregler auf die empfohlenen Startwerte zurueck."
        )
        reset_button.clicked.connect(self.reset_defaults)

        layout = QVBoxLayout()
        layout.addWidget(info_label)
        layout.addWidget(self._build_preset_selector())
        layout.addLayout(slider_grid)
        layout.addWidget(reset_button)
        self.setLayout(layout)

    def _build_preset_selector(self) -> QComboBox:
        preset_selector = QComboBox()
        preset_selector.addItems(PRESETS.keys())
        preset_selector.addItem(AUTO_PRESET_LABEL)
        preset_selector.addItem(GUIDED_PRESET_LABEL)
        preset_selector.addItem(CUSTOM_PRESET_LABEL)
        preset_selector.setToolTip(
            "Startwerte fuer typische Bildsituationen. Danach kannst du fein nachregeln."
        )
        preset_selector.currentTextChanged.connect(self.apply_preset)
        self.preset_selector = preset_selector
        return preset_selector

    def analysis_settings(
        self,
        manual_petri_circle: tuple[int, int, int] | None = None,
        excluded_component_points: tuple[tuple[int, int], ...] = (),
        manual_leaf_points: tuple[tuple[int, int], ...] = (),
        manual_leaf_radius_px: int = 14,
        manual_leaf_patches: tuple[tuple[int, int, int], ...] = (),
    ) -> AnalysisSettings:
        return AnalysisSettings(
            thresholds=self.thresholds(),
            min_object_area_px=self._value("min_object_area_px"),
            max_object_area_px=self._value("max_object_area_px"),
            green_dominance_margin=self._value("green_dominance_margin"),
            green_index_min=self._value("green_index_min"),
            leaf_fill_px=self._value("leaf_fill_px"),
            pale_leaf_expansion_px=self._value("pale_leaf_expansion_px"),
            root_trim_px=self._value("root_trim_px"),
            inner_dish_factor=self._value("inner_dish_percent") / 100.0,
            manual_petri_circle=manual_petri_circle,
            excluded_component_points=excluded_component_points,
            manual_leaf_points=manual_leaf_points,
            manual_leaf_radius_px=manual_leaf_radius_px,
            manual_leaf_patches=manual_leaf_patches,
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
        self.set_analysis_settings(PRESETS["Standard"], preset_name="Standard")

    def apply_preset(self, preset_name: str) -> None:
        preset = PRESETS.get(preset_name)
        if preset is None:
            return
        self.set_analysis_settings(preset, preset_name=preset_name)

    def set_analysis_settings(
        self,
        settings: AnalysisSettings,
        preset_name: str = CUSTOM_PRESET_LABEL,
    ) -> None:
        values = self._slider_values_from_settings(settings)
        blockers = [QSignalBlocker(slider) for slider in self._sliders.values()]
        try:
            for name, value in values.items():
                self._sliders[name].setValue(value)
                self._value_labels[name].setText(str(value))
        finally:
            del blockers
        self._set_preset_label(preset_name)
        self.settings_changed.emit(self.analysis_settings())

    def _slider_values_from_settings(self, settings: AnalysisSettings) -> dict[str, int]:
        thresholds = settings.thresholds
        return {
            "h_min": thresholds.h_min,
            "h_max": thresholds.h_max,
            "s_min": thresholds.s_min,
            "s_max": thresholds.s_max,
            "v_min": thresholds.v_min,
            "v_max": thresholds.v_max,
            "min_object_area_px": settings.min_object_area_px,
            "max_object_area_px": settings.max_object_area_px,
            "green_dominance_margin": settings.green_dominance_margin,
            "green_index_min": settings.green_index_min,
            "leaf_fill_px": settings.leaf_fill_px,
            "pale_leaf_expansion_px": settings.pale_leaf_expansion_px,
            "root_trim_px": settings.root_trim_px,
            "inner_dish_percent": int(round(settings.inner_dish_factor * 100)),
        }

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
        self._set_preset_label(CUSTOM_PRESET_LABEL)
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

    def _set_preset_label(self, preset_name: str) -> None:
        index = self.preset_selector.findText(preset_name)
        if index < 0:
            return

        blocker = QSignalBlocker(self.preset_selector)
        try:
            self.preset_selector.setCurrentIndex(index)
        finally:
            del blocker
