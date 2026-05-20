from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from analysis.green_segmentation import analyze_green_area
from app.image_viewer import ImageViewer
from app.results_table import ResultsTable
from app.settings_panel import SettingsPanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PlantAreaAnalyzer")
        self.resize(1200, 720)
        self.current_image_path: Optional[Path] = None

        load_button = QPushButton("Bild laden")
        load_button.clicked.connect(self.load_image)

        self.original_viewer = ImageViewer("Noch kein Bild geladen")
        self.result_viewer = ImageViewer("Maske oder Overlay wird hier angezeigt")
        self.results_table = ResultsTable()
        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_changed.connect(self.reanalyze_current_image)

        image_layout = QHBoxLayout()
        image_layout.addWidget(self.original_viewer)
        image_layout.addWidget(self.result_viewer)

        right_layout = QVBoxLayout()
        right_layout.addWidget(load_button)
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
        self.reanalyze_current_image()

    def reanalyze_current_image(self) -> None:
        if self.current_image_path is None:
            return

        try:
            result = analyze_green_area(
                self.current_image_path,
                settings=self.settings_panel.analysis_settings(),
            )
        except Exception as error:  # noqa: BLE001
            QMessageBox.critical(self, "Analysefehler", str(error))
            return

        self.original_viewer.set_image(result.original_qimage)
        self.result_viewer.set_image(result.overlay_qimage)
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


def run() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
