from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from analysis.settings import AnalysisSettings
from app.settings_panel import PRESETS


def build_guided_settings(
    *,
    dark_medium: bool,
    roots_or_halos: bool,
    pale_leaves_missing: bool,
    small_noise: bool,
    rim_artifacts: bool,
) -> tuple[str, AnalysisSettings]:
    """Return a preset-like recommendation from beginner-friendly questions."""
    if roots_or_halos and pale_leaves_missing:
        preset_name = "Blasse Blattbasis + Wurzeln streng"
    elif dark_medium and roots_or_halos:
        preset_name = "Dunkle Blaetter + Wurzeln streng"
    elif dark_medium:
        preset_name = "Dunkle Blaetter"
    elif roots_or_halos:
        preset_name = "Streng gegen Wurzeln"
    elif pale_leaves_missing:
        preset_name = "Blasse Blaetter"
    else:
        preset_name = "Standard"

    settings = PRESETS[preset_name]

    if pale_leaves_missing and roots_or_halos:
        # Controlled expansion: recover pale leaf bases without opening the door too far.
        settings = replace(
            settings,
            pale_leaf_expansion_px=max(settings.pale_leaf_expansion_px, 32),
            root_trim_px=max(settings.root_trim_px, 8),
        )
    elif roots_or_halos:
        settings = replace(
            settings,
            green_dominance_margin=min(settings.green_dominance_margin, 10),
            green_index_min=max(settings.green_index_min, 80),
            leaf_fill_px=0,
            pale_leaf_expansion_px=max(settings.pale_leaf_expansion_px, 18),
            root_trim_px=max(settings.root_trim_px, 10),
        )
    elif pale_leaves_missing:
        settings = replace(
            settings,
            pale_leaf_expansion_px=max(settings.pale_leaf_expansion_px, 20),
        )

    if small_noise:
        settings = replace(
            settings,
            min_object_area_px=min(settings.min_object_area_px + 160, 2500),
        )

    if rim_artifacts:
        settings = replace(settings, inner_dish_factor=min(settings.inner_dish_factor, 0.84))

    return preset_name, settings


class GuidedSettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gefuehrte Einstellungen")

        intro_label = QLabel(
            "Beantworte die Fragen nach dem sichtbaren Problem. "
            "Die App setzt daraus sinnvolle Startwerte, danach kannst du fein nachregeln."
        )
        intro_label.setWordWrap(True)

        self.dark_medium_checkbox = QCheckBox(
            "Das Medium ist dunkel oder die Blaetter sind wenig leuchtend."
        )
        self.roots_or_halos_checkbox = QCheckBox(
            "Wurzeln, helle Saeume oder Medium werden faelschlich mit erkannt."
        )
        self.pale_leaves_checkbox = QCheckBox(
            "Blasse/gelbliche Blattteile oder graugruene Blattbasis fehlen."
        )
        self.small_noise_checkbox = QCheckBox(
            "Viele kleine Stoerpunkte oder Kruemel werden erkannt."
        )
        self.rim_artifacts_checkbox = QCheckBox(
            "Rand, Glas oder Schalen-Schatten stoeren die Analyse."
        )

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(intro_label)
        layout.addWidget(self.dark_medium_checkbox)
        layout.addWidget(self.roots_or_halos_checkbox)
        layout.addWidget(self.pale_leaves_checkbox)
        layout.addWidget(self.small_noise_checkbox)
        layout.addWidget(self.rim_artifacts_checkbox)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def recommended_settings(self) -> tuple[str, AnalysisSettings]:
        return build_guided_settings(
            dark_medium=self.dark_medium_checkbox.isChecked(),
            roots_or_halos=self.roots_or_halos_checkbox.isChecked(),
            pale_leaves_missing=self.pale_leaves_checkbox.isChecked(),
            small_noise=self.small_noise_checkbox.isChecked(),
            rim_artifacts=self.rim_artifacts_checkbox.isChecked(),
        )
