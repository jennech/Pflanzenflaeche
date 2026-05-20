from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.image_viewer import ImageViewer
from app.results_table import ResultsTable
from app.settings_panel import SettingsPanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PlantAreaAnalyzer")
        self.resize(1200, 720)
        self.current_image_path: Optional[Path] = None
        self.current_petri_circle: Optional[tuple[int, int, int]] = None
        self.manual_petri_circle: Optional[tuple[int, int, int]] = None

        load_button = QPushButton("Bild laden")
        load_button.clicked.connect(self.load_image)

        self.original_viewer = ImageViewer("Noch kein Bild geladen")
        self.original_viewer.circle_selected.connect(self.set_manual_petri_circle)
        self.result_viewer = ImageViewer("Maske oder Overlay wird hier angezeigt")
        self.results_table = ResultsTable()
        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_changed.connect(self.reanalyze_current_image)

        self.show_petri_checkbox = QCheckBox("Petrischale anzeigen")
        self.show_petri_checkbox.setChecked(True)
        self.show_petri_checkbox.toggled.connect(self.update_petri_overlay)

        self.manual_petri_checkbox = QCheckBox("Petrischale manuell setzen")
        self.manual_petri_checkbox.toggled.connect(self.toggle_manual_petri_mode)

        image_layout = QHBoxLayout()
        image_layout.addWidget(self.original_viewer)
        image_layout.addWidget(self.result_viewer)

        right_layout = QVBoxLayout()
        right_layout.addWidget(load_button)
        right_layout.addWidget(self.show_petri_checkbox)
        right_layout.addWidget(self.manual_petri_checkbox)
        right_layout.addWidget(self.settings_panel)
        right_layout.addWidget(self.results_table)
        right_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.addLayout(image_layout, stretch=3)
        main_layout.addLayout(right_layout, stretch=1)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def load_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Bild auswaehlen",
            "",
            "Bilddateien (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )

        if not file_path:
            return

        self.current_image_path = Path(file_path)
        self.current_petri_circle = None
        self.manual_petri_circle = None
        self.reanalyze_current_image()

    def reanalyze_current_image(self) -> None:
        if self.current_image_path is None:
            return

        try:
            from analysis.green_segmentation import analyze_green_area

            result = analyze_green_area(
                self.current_image_path,
                settings=self.settings_panel.analysis_settings(
                    manual_petri_circle=self.manual_petri_circle,
                ),
            )
        except Exception as error:  # noqa: BLE001
            QMessageBox.critical(self, "Analysefehler", str(error))
            return

        self.original_viewer.set_image(result.original_qimage)
        self.result_viewer.set_image(result.overlay_qimage)
        self.current_petri_circle = (
            result.petri_circle.center_x,
            result.petri_circle.center_y,
            result.petri_circle.radius,
        )
        self.update_petri_overlay()
        self.results_table.update_results(
            {
                "Gruene Pixel": f"{result.measurement.green_pixels}",
                "Petrischalenflaeche": (
                    f"{result.measurement.petri_area_mm2:.2f} mm^2"
                ),
                "Pflanzenflaeche": (
                    f"{result.measurement.green_area_mm2:.2f} mm^2"
                ),
                "Flaechenbedeckung": (
                    f"{result.measurement.coverage_percent:.2f} %"
                ),
            }
        )

    def set_manual_petri_circle(self, circle: tuple[int, int, int]) -> None:
        self.manual_petri_circle = circle
        self.manual_petri_checkbox.setChecked(True)
        self.reanalyze_current_image()

    def toggle_manual_petri_mode(self, enabled: bool) -> None:
        self.original_viewer.set_manual_circle_enabled(enabled)
        if not enabled:
            self.manual_petri_circle = None
            self.reanalyze_current_image()

    def update_petri_overlay(self) -> None:
        visible = self.show_petri_checkbox.isChecked()
        circle = self.manual_petri_circle or self.current_petri_circle
        self.original_viewer.set_petri_circle(circle, visible)
        self.result_viewer.set_petri_circle(circle, visible)


def run() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
