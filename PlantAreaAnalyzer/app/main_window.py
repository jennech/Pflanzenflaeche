from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QByteArray, QSettings, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
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
        self._settings = QSettings("Kojla", "PlantAreaAnalyzer")
        self.current_image_path: Optional[Path] = None
        self.current_analysis_result = None
        self.current_petri_circle: Optional[tuple[int, int, int]] = None
        self.manual_petri_circle: Optional[tuple[int, int, int]] = None
        self.excluded_component_points: list[tuple[int, int]] = []
        self.manual_leaf_points: list[tuple[int, int]] = []

        load_button = QPushButton("Bild laden")
        load_button.clicked.connect(self.load_image)
        self.csv_export_button = QPushButton("CSV speichern")
        self.csv_export_button.setEnabled(False)
        self.csv_export_button.clicked.connect(self.save_csv_export)
        self.auto_settings_button = QPushButton("Werte vorschlagen")
        self.auto_settings_button.setEnabled(False)
        self.auto_settings_button.clicked.connect(self.suggest_settings_for_current_image)
        self.guided_settings_button = QPushButton("Gefuehrt einstellen")
        self.guided_settings_button.clicked.connect(self.open_guided_settings)
        self.filename_label = QLabel("Datei: noch kein Bild geladen")
        self.filename_label.setWordWrap(True)
        self.filename_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.original_viewer = ImageViewer("Noch kein Bild geladen")
        self.original_viewer.circle_selected.connect(self.set_manual_petri_circle)
        self.original_viewer.point_selected.connect(self.exclude_component_at_point)
        self.original_viewer.add_point_selected.connect(self.add_leaf_area_at_point)
        self.result_viewer = ImageViewer("Maske oder Overlay wird hier angezeigt")
        self.result_viewer.point_selected.connect(self.exclude_component_at_point)
        self.result_viewer.add_point_selected.connect(self.add_leaf_area_at_point)
        self.results_table = ResultsTable()
        self.settings_panel = SettingsPanel()
        self.settings_panel.settings_changed.connect(self.reanalyze_current_image)
        self.build_menu_bar()

        self.show_petri_checkbox = QCheckBox("Petrischale anzeigen")
        self.show_petri_checkbox.setChecked(True)
        self.show_petri_checkbox.toggled.connect(self.update_petri_overlay)

        self.manual_petri_checkbox = QCheckBox("Petrischale manuell setzen")
        self.manual_petri_checkbox.toggled.connect(self.toggle_manual_petri_mode)

        self.exclude_component_checkbox = QCheckBox("Stoerflaeche per Klick entfernen")
        self.exclude_component_checkbox.toggled.connect(self.toggle_exclusion_mode)
        reset_exclusions_button = QPushButton("Entfernte Flaechen zuruecksetzen")
        reset_exclusions_button.clicked.connect(self.reset_excluded_components)
        self.add_leaf_checkbox = QCheckBox("Blattflaeche per Klick hinzufuegen")
        self.add_leaf_checkbox.toggled.connect(self.toggle_add_leaf_mode)
        reset_added_leaf_button = QPushButton("Hinzugefuegte Flaechen zuruecksetzen")
        reset_added_leaf_button.clicked.connect(self.reset_added_leaf_area)

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

        self.results_toggle = QToolButton()
        self.results_toggle.setText("Ergebnisse ausblenden")
        self.results_toggle.setCheckable(True)
        self.results_toggle.setChecked(True)
        self.results_toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.results_toggle.setArrowType(Qt.DownArrow)
        self.results_toggle.toggled.connect(self.toggle_results_panel)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(8)
        right_layout.addWidget(load_button)
        right_layout.addWidget(self.filename_label)
        right_layout.addWidget(self.csv_export_button)
        right_layout.addWidget(self.auto_settings_button)
        right_layout.addWidget(self.guided_settings_button)
        right_layout.addWidget(self.show_petri_checkbox)
        right_layout.addWidget(self.manual_petri_checkbox)
        right_layout.addWidget(self.exclude_component_checkbox)
        right_layout.addWidget(reset_exclusions_button)
        right_layout.addWidget(self.add_leaf_checkbox)
        right_layout.addWidget(reset_added_leaf_button)
        right_layout.addWidget(self.manual_adjust_toggle)
        right_layout.addWidget(self.manual_adjust_panel)
        right_layout.addWidget(self.settings_panel)

        controls_widget = QWidget()
        controls_widget.setLayout(right_layout)

        self.controls_scroll = QScrollArea()
        self.controls_scroll.setWidgetResizable(True)
        self.controls_scroll.setWidget(controls_widget)
        self.controls_scroll.setMinimumHeight(240)

        self.results_panel = QWidget()
        self.results_panel.setMinimumHeight(170)
        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.addWidget(self.results_toggle)
        results_layout.addWidget(self.results_table)
        self.results_panel.setLayout(results_layout)
        self.results_table.setMinimumHeight(130)

        self.right_splitter = QSplitter(Qt.Vertical)
        self.right_splitter.addWidget(self.controls_scroll)
        self.right_splitter.addWidget(self.results_panel)
        self.right_splitter.setSizes([500, 220])
        self.right_splitter.setStretchFactor(0, 1)
        self.right_splitter.setStretchFactor(1, 0)
        self.right_splitter.setCollapsible(0, False)
        self.right_splitter.setCollapsible(1, False)

        self.image_splitter = QSplitter(Qt.Horizontal)
        self.image_splitter.addWidget(self.original_viewer)
        self.image_splitter.addWidget(self.result_viewer)
        self.image_splitter.setSizes([560, 560])
        self.image_splitter.setStretchFactor(0, 1)
        self.image_splitter.setStretchFactor(1, 1)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.image_splitter)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([880, 320])
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 1)

        self.setCentralWidget(self.main_splitter)
        self.restore_saved_layout()

    def build_menu_bar(self) -> None:
        analysis_menu = self.menuBar().addMenu("Analyse")
        guided_action = QAction("Gefuehrte Einstellungen...", self)
        guided_action.triggered.connect(self.open_guided_settings)
        analysis_menu.addAction(guided_action)

        auto_action = QAction("Werte vorschlagen", self)
        auto_action.triggered.connect(self.suggest_settings_for_current_image)
        analysis_menu.addAction(auto_action)

    def restore_saved_layout(self) -> None:
        geometry = self._settings.value("window/geometry")
        geometry_data = self._to_qbytearray(geometry)
        if geometry_data is not None:
            self.restoreGeometry(geometry_data)

        for key, splitter in (
            ("splitter/main", self.main_splitter),
            ("splitter/images", self.image_splitter),
            ("splitter/right", self.right_splitter),
        ):
            splitter_state = self._to_qbytearray(self._settings.value(key))
            if splitter_state is not None:
                splitter.restoreState(splitter_state)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("splitter/main", self.main_splitter.saveState())
        self._settings.setValue("splitter/images", self.image_splitter.saveState())
        self._settings.setValue("splitter/right", self.right_splitter.saveState())
        super().closeEvent(event)

    @staticmethod
    def _to_qbytearray(value: object) -> QByteArray | None:
        if isinstance(value, QByteArray):
            return value
        if isinstance(value, (bytes, bytearray)):
            return QByteArray(value)
        return None

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

    def toggle_results_panel(self, expanded: bool) -> None:
        self.results_table.setVisible(expanded)
        self.results_toggle.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)
        self.results_toggle.setText(
            "Ergebnisse ausblenden" if expanded else "Ergebnisse anzeigen"
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
        self.update_filename_display()
        self.current_analysis_result = None
        self.csv_export_button.setEnabled(False)
        self.auto_settings_button.setEnabled(True)
        self.current_petri_circle = None
        self.manual_petri_circle = None
        self.excluded_component_points = []
        self.manual_leaf_points = []
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
                    manual_leaf_points=tuple(self.manual_leaf_points),
                ),
            )
        except Exception as error:  # noqa: BLE001
            QMessageBox.critical(self, "Analysefehler", str(error))
            return

        self.current_analysis_result = result
        self.csv_export_button.setEnabled(True)
        self.original_viewer.set_image(result.original_qimage)
        self.result_viewer.set_image(result.overlay_qimage)
        self.current_petri_circle = (
            result.petri_circle.center_x,
            result.petri_circle.center_y,
            result.petri_circle.radius,
        )
        self.update_petri_overlay()
        self.update_exclusion_markers()
        self.update_addition_markers()
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

    def save_csv_export(self) -> None:
        if self.current_image_path is None or self.current_analysis_result is None:
            QMessageBox.information(
                self,
                "CSV speichern",
                "Bitte zuerst ein Bild laden und analysieren.",
            )
            return

        file_path = self.select_csv_export_path()
        if not file_path:
            return

        csv_path = Path(file_path)
        if csv_path.suffix.lower() != ".csv":
            csv_path = csv_path.with_suffix(".csv")

        try:
            from exports.export_csv import export_analysis_to_csv

            export_analysis_to_csv(
                csv_path=csv_path,
                image_path=self.current_image_path,
                measurement=self.current_analysis_result.measurement,
                petri_circle=self.current_analysis_result.petri_circle,
                settings=self.settings_panel.analysis_settings(
                    manual_petri_circle=self.manual_petri_circle,
                    excluded_component_points=tuple(self.excluded_component_points),
                    manual_leaf_points=tuple(self.manual_leaf_points),
                ),
            )
        except Exception as error:  # noqa: BLE001
            QMessageBox.critical(self, "CSV-Fehler", str(error))
            return

        QMessageBox.information(
            self,
            "CSV gespeichert",
            f"Ergebnis wurde an die CSV angehaengt:\n{csv_path}",
        )

    def select_csv_export_path(self) -> str:
        dialog = QFileDialog(self, "CSV speichern oder erweitern")
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilter("CSV-Dateien (*.csv)")
        dialog.setDefaultSuffix("csv")
        dialog.setOption(QFileDialog.DontConfirmOverwrite, True)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setLabelText(QFileDialog.Accept, "Speichern/anhaengen")
        if not dialog.exec():
            return ""

        selected_files = dialog.selectedFiles()
        return selected_files[0] if selected_files else ""

    def suggest_settings_for_current_image(self) -> None:
        if self.current_image_path is None:
            QMessageBox.information(
                self,
                "Werte vorschlagen",
                "Bitte zuerst ein Bild laden.",
            )
            return

        try:
            from analysis.auto_settings import suggest_analysis_settings

            suggested_settings = suggest_analysis_settings(
                image_path=self.current_image_path,
                base_settings=self.settings_panel.analysis_settings(
                    manual_petri_circle=self.manual_petri_circle,
                    excluded_component_points=tuple(self.excluded_component_points),
                    manual_leaf_points=tuple(self.manual_leaf_points),
                ),
                manual_petri_circle=self.manual_petri_circle,
            )
        except Exception as error:  # noqa: BLE001
            QMessageBox.critical(self, "Vorschlag fehlgeschlagen", str(error))
            return

        self.settings_panel.set_analysis_settings(
            suggested_settings,
            preset_name="Auto-Vorschlag",
        )

    def open_guided_settings(self) -> None:
        from app.guided_settings_dialog import GuidedSettingsDialog
        from app.settings_panel import GUIDED_PRESET_LABEL

        dialog = GuidedSettingsDialog(self)
        if not dialog.exec():
            return

        _, settings = dialog.recommended_settings()
        self.settings_panel.set_analysis_settings(
            settings,
            preset_name=GUIDED_PRESET_LABEL,
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
        if enabled and self.add_leaf_checkbox.isChecked():
            self.add_leaf_checkbox.setChecked(False)
        self.original_viewer.set_manual_circle_enabled(enabled)
        self.result_viewer.set_manual_circle_enabled(False)
        if not enabled:
            self.manual_petri_circle = None
            self.reanalyze_current_image()

    def toggle_exclusion_mode(self, enabled: bool) -> None:
        if enabled and self.manual_petri_checkbox.isChecked():
            self.manual_petri_checkbox.setChecked(False)
        if enabled and self.add_leaf_checkbox.isChecked():
            self.add_leaf_checkbox.setChecked(False)
        self.original_viewer.set_exclusion_mode_enabled(enabled)
        self.result_viewer.set_exclusion_mode_enabled(enabled)

    def toggle_add_leaf_mode(self, enabled: bool) -> None:
        if enabled and self.manual_petri_checkbox.isChecked():
            self.manual_petri_checkbox.setChecked(False)
        if enabled and self.exclude_component_checkbox.isChecked():
            self.exclude_component_checkbox.setChecked(False)
        self.original_viewer.set_addition_mode_enabled(enabled)
        self.result_viewer.set_addition_mode_enabled(enabled)

    def exclude_component_at_point(self, point: tuple[int, int]) -> None:
        self.excluded_component_points.append(point)
        self.reanalyze_current_image()

    def add_leaf_area_at_point(self, point: tuple[int, int]) -> None:
        self.manual_leaf_points.append(point)
        self.reanalyze_current_image()

    def reset_excluded_components(self) -> None:
        if not self.excluded_component_points:
            return

        self.excluded_component_points = []
        self.reanalyze_current_image()

    def reset_added_leaf_area(self) -> None:
        if not self.manual_leaf_points:
            return

        self.manual_leaf_points = []
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
        self.update_addition_markers()

    def update_exclusion_markers(self) -> None:
        self.original_viewer.set_exclusion_points(self.excluded_component_points)
        self.result_viewer.set_exclusion_points(self.excluded_component_points)

    def update_addition_markers(self) -> None:
        self.original_viewer.set_addition_points(self.manual_leaf_points)
        self.result_viewer.set_addition_points(self.manual_leaf_points)

    def update_filename_display(self) -> None:
        if self.current_image_path is None:
            self.filename_label.setText("Datei: noch kein Bild geladen")
            self.filename_label.setToolTip("")
            self.setWindowTitle("PlantAreaAnalyzer")
            return

        filename = self.current_image_path.name
        self.filename_label.setText(f"Datei: {filename}")
        self.filename_label.setToolTip(str(self.current_image_path))
        self.setWindowTitle(f"PlantAreaAnalyzer - {filename}")

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
