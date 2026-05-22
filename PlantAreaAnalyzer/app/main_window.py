from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.image_viewer import ImageViewer
from app.results_table import ResultsTable
from app.settings_panel import SettingsPanel


class MainWindow(QMainWindow):
    PETRI_NUDGE_STEP_PX = 5
    PETRI_RADIUS_STEP_PX = 5

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PlantAreaAnalyzer")
        self.resize(1200, 720)
        self.current_image_path: Optional[Path] = None
        self.current_petri_circle: Optional[tuple[int, int, int]] = None
        self.manual_petri_circle: Optional[tuple[int, int, int]] = None
        self.excluded_component_points: list[tuple[int, int]] = []

        load_button = QPushButton("Bild laden")
        load_button.clicked.connect(self.load_image)

        self.original_viewer = ImageViewer("Noch kein Bild geladen")
        self.original_viewer.circle_selected.connect(self.set_manual_petri_circle)
        self.original_viewer.point_selected.connect(self.exclude_component_at_point)
        self.result_viewer = ImageViewer("Maske oder Overlay wird hier angezeigt")
        self.result_viewer.point_selected.connect(self.exclude_component_at_point)
        self.results_table = ResultsTable()
        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_changed.connect(self.reanalyze_current_image)

        self.show_petri_checkbox = QCheckBox("Petrischale anzeigen")
        self.show_petri_checkbox.setChecked(True)
        self.show_petri_checkbox.toggled.connect(self.update_petri_overlay)

        self.manual_petri_checkbox = QCheckBox("Petrischale manuell setzen")
        self.manual_petri_checkbox.toggled.connect(self.toggle_manual_petri_mode)

        self.exclude_component_checkbox = QCheckBox("Stoerflaeche per Klick entfernen")
        self.exclude_component_checkbox.toggled.connect(self.toggle_exclusion_mode)
        reset_exclusions_button = QPushButton("Entfernte Flaechen zuruecksetzen")
        reset_exclusions_button.clicked.connect(self.reset_excluded_components)

        self.manual_adjust_toggle = QToolButton()
        self.manual_adjust_toggle.setText("Manuelle Korrektur anzeigen")
        self.manual_adjust_toggle.setCheckable(True)
        self.manual_adjust_toggle.setChecked(False)
        self.manual_adjust_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.manual_adjust_toggle.setArrowType(Qt.RightArrow)
        self.manual_adjust_toggle.toggled.connect(self.toggle_manual_adjust_panel)

        self.manual_adjust_panel = QWidget()
        self.manual_adjust_panel.setLayout(self.build_manual_adjust_layout())
        self.manual_adjust_panel.setVisible(False)

        right_layout = QVBoxLayout()
        right_layout.addWidget(load_button)
        right_layout.addWidget(self.show_petri_checkbox)
        right_layout.addWidget(self.manual_petri_checkbox)
        right_layout.addWidget(self.exclude_component_checkbox)
        right_layout.addWidget(reset_exclusions_button)
        right_layout.addWidget(self.manual_adjust_toggle)
        right_layout.addWidget(self.manual_adjust_panel)
        right_layout.addWidget(self.settings_panel)
        right_layout.addStretch()

        controls_widget = QWidget()
        controls_widget.setLayout(right_layout)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(controls_widget)
        right_splitter.addWidget(self.results_table)
        right_splitter.setSizes([560, 220])
        right_splitter.setStretchFactor(0, 2)
        right_splitter.setStretchFactor(1, 1)

        image_splitter = QSplitter(Qt.Horizontal)
        image_splitter.addWidget(self.original_viewer)
        image_splitter.addWidget(self.result_viewer)
        image_splitter.setSizes([560, 560])
        image_splitter.setStretchFactor(0, 1)
        image_splitter.setStretchFactor(1, 1)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(image_splitter)
        main_splitter.addWidget(right_splitter)
        main_splitter.setSizes([880, 320])
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 1)

        self.setCentralWidget(main_splitter)

    def build_manual_adjust_layout(self) -> QGridLayout:
        layout = QGridLayout()

        up_button = QPushButton("Hoch")
        down_button = QPushButton("Runter")
        left_button = QPushButton("Links")
        right_button = QPushButton("Rechts")
        radius_smaller_button = QPushButton("Radius -")
        radius_larger_button = QPushButton("Radius +")

        up_button.clicked.connect(
            lambda: self.adjust_manual_petri_circle(dy=-self.PETRI_NUDGE_STEP_PX)
        )
        down_button.clicked.connect(
            lambda: self.adjust_manual_petri_circle(dy=self.PETRI_NUDGE_STEP_PX)
        )
        left_button.clicked.connect(
            lambda: self.adjust_manual_petri_circle(dx=-self.PETRI_NUDGE_STEP_PX)
        )
        right_button.clicked.connect(
            lambda: self.adjust_manual_petri_circle(dx=self.PETRI_NUDGE_STEP_PX)
        )
        radius_smaller_button.clicked.connect(
            lambda: self.adjust_manual_petri_circle(dr=-self.PETRI_RADIUS_STEP_PX)
        )
        radius_larger_button.clicked.connect(
            lambda: self.adjust_manual_petri_circle(dr=self.PETRI_RADIUS_STEP_PX)
        )

        layout.addWidget(up_button, 0, 1)
        layout.addWidget(left_button, 1, 0)
        layout.addWidget(right_button, 1, 2)
        layout.addWidget(down_button, 2, 1)
        layout.addWidget(radius_smaller_button, 3, 0)
        layout.addWidget(radius_larger_button, 3, 2)
        return layout

    def toggle_manual_adjust_panel(self, expanded: bool) -> None:
        self.manual_adjust_panel.setVisible(expanded)
        self.manual_adjust_toggle.setArrowType(
            Qt.DownArrow if expanded else Qt.RightArrow
        )
        self.manual_adjust_toggle.setText(
            "Manuelle Korrektur ausblenden"
            if expanded
            else "Manuelle Korrektur anzeigen"
        )

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
        self.excluded_component_points = []
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
                    excluded_component_points=tuple(self.excluded_component_points),
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
        self.update_exclusion_markers()
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

    def adjust_manual_petri_circle(
        self,
        dx: int = 0,
        dy: int = 0,
        dr: int = 0,
    ) -> None:
        base_circle = self.manual_petri_circle or self.current_petri_circle
        if base_circle is None:
            return

        center_x, center_y, radius = base_circle
        self.manual_petri_circle = (
            max(0, center_x + dx),
            max(0, center_y + dy),
            max(1, radius + dr),
        )
        if not self.manual_petri_checkbox.isChecked():
            self.manual_petri_checkbox.setChecked(True)
        self.reanalyze_current_image()

    def toggle_manual_petri_mode(self, enabled: bool) -> None:
        if enabled and self.exclude_component_checkbox.isChecked():
            self.exclude_component_checkbox.setChecked(False)
        self.original_viewer.set_manual_circle_enabled(enabled)
        self.result_viewer.set_manual_circle_enabled(False)
        if not enabled:
            self.manual_petri_circle = None
            self.reanalyze_current_image()

    def toggle_exclusion_mode(self, enabled: bool) -> None:
        if enabled and self.manual_petri_checkbox.isChecked():
            self.manual_petri_checkbox.setChecked(False)
        self.original_viewer.set_exclusion_mode_enabled(enabled)
        self.result_viewer.set_exclusion_mode_enabled(enabled)

    def exclude_component_at_point(self, point: tuple[int, int]) -> None:
        self.excluded_component_points.append(point)
        self.reanalyze_current_image()

    def reset_excluded_components(self) -> None:
        if not self.excluded_component_points:
            return

        self.excluded_component_points = []
        self.reanalyze_current_image()

    def update_petri_overlay(self) -> None:
        visible = self.show_petri_checkbox.isChecked()
        circle = self.manual_petri_circle or self.current_petri_circle
        analysis_circle = self.analysis_overlay_circle(circle)
        self.original_viewer.set_petri_circle(circle, visible)
        self.result_viewer.set_petri_circle(circle, visible)
        self.original_viewer.set_analysis_circle(analysis_circle, visible)
        self.result_viewer.set_analysis_circle(analysis_circle, visible)
        self.update_exclusion_markers()

    def update_exclusion_markers(self) -> None:
        self.original_viewer.set_exclusion_points(self.excluded_component_points)
        self.result_viewer.set_exclusion_points(self.excluded_component_points)

    def analysis_overlay_circle(
        self,
        circle: tuple[int, int, int] | None,
    ) -> tuple[int, int, int] | None:
        if circle is None:
            return None

        center_x, center_y, radius = circle
        inner_radius = max(1, int(round(radius * self.settings_panel.inner_dish_factor())))
        return (center_x, center_y, inner_radius)


def run() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
