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
        self._add_slider(slider_grid, "Gruen-Abstand", "green_dominance_margin", 0, 80, 12, 7)
        self._add_slider(slider_grid, "Innenradius %", "inner_dish_percent", 75, 100, 90, 8)

        reset_button = QPushButton("Standardwerte")
        reset_button.clicked.connect(self.reset_defaults)

        layout = QVBoxLayout()
        layout.addWidget(info_label)
        layout.addLayout(slider_grid)
        layout.addWidget(reset_button)
        self.setLayout(layout)

    def analysis_settings(self) -> AnalysisSettings:
        return AnalysisSettings(
            thresholds=self.thresholds(),
            min_object_area_px=self._value("min_object_area_px"),
            green_dominance_margin=self._value("green_dominance_margin"),
            inner_dish_factor=self._value("inner_dish_percent") / 100.0,
        )

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
            "green_dominance_margin": 12,
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
        value_label = QLabel(str(value))
        value_label.setMinimumWidth(32)
        value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(value)
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
