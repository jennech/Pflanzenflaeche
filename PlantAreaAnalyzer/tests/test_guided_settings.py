from __future__ import annotations

from app.guided_settings_dialog import build_guided_settings


def test_guided_settings_prefers_dark_root_preset() -> None:
    preset_name, settings = build_guided_settings(
        dark_medium=True,
        roots_or_halos=True,
        pale_leaves_missing=False,
        small_noise=False,
        rim_artifacts=False,
    )

    assert preset_name == "Dunkle Blaetter + Wurzeln streng"
    assert settings.thresholds.s_min >= 150
    assert settings.green_dominance_margin <= 10
    assert settings.green_index_min >= 80
    assert settings.leaf_fill_px == 0
    assert settings.pale_leaf_expansion_px >= 18
    assert settings.root_trim_px >= 10


def test_guided_settings_combines_pale_and_root_constraints() -> None:
    preset_name, settings = build_guided_settings(
        dark_medium=False,
        roots_or_halos=True,
        pale_leaves_missing=True,
        small_noise=True,
        rim_artifacts=True,
    )

    assert preset_name == "Streng gegen Wurzeln"
    assert settings.leaf_fill_px == 0
    assert settings.pale_leaf_expansion_px >= 18
    assert settings.root_trim_px >= 10
    assert settings.min_object_area_px > 300
    assert settings.inner_dish_factor <= 0.84


def test_guided_settings_uses_pale_preset_when_leaves_are_missing() -> None:
    preset_name, settings = build_guided_settings(
        dark_medium=False,
        roots_or_halos=False,
        pale_leaves_missing=True,
        small_noise=False,
        rim_artifacts=False,
    )

    assert preset_name == "Blasse Blaetter"
    assert settings.thresholds.s_min <= 30
    assert settings.pale_leaf_expansion_px >= 20
