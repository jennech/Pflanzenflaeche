from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pytest

import analysis.auto_settings as auto_settings
from analysis.auto_settings import build_leaf_candidate_mask
from analysis.auto_settings import reference_settings_is_plausible_for_image
from analysis.auto_settings import suggest_analysis_settings
from analysis.settings import AnalysisSettings
from analysis.settings import HSVThresholds


def test_auto_settings_suggests_leaf_friendly_thresholds(tmp_path: Path) -> None:
    image = np.full((180, 180, 3), [40, 36, 30], dtype=np.uint8)
    cv2.circle(image, (90, 90), 80, [38, 34, 28], -1)
    for center in [(62, 62), (118, 62), (62, 118), (118, 118)]:
        cv2.circle(image, center, 13, [45, 85, 42], -1)
        cv2.circle(image, center, 6, [52, 105, 48], -1)

    # A thin root-like structure should not dominate the suggested settings.
    cv2.line(image, (60, 75), (30, 95), [150, 160, 150], 1)
    image_path = tmp_path / "dark_plate.png"
    cv2.imwrite(str(image_path), image)

    settings = suggest_analysis_settings(
        image_path,
        manual_petri_circle=(90, 90, 80),
    )

    assert settings.thresholds.h_min <= 70
    assert settings.thresholds.h_max >= 70
    assert settings.thresholds.s_min <= 185
    assert settings.pale_leaf_expansion_px <= 30
    assert settings.min_object_area_px >= 80


def test_leaf_candidate_mask_ignores_thin_root_like_components() -> None:
    image = np.full((80, 80, 3), [40, 36, 30], dtype=np.uint8)
    cv2.circle(image, (28, 28), 10, [45, 85, 42], -1)
    cv2.line(image, (10, 55), (70, 55), [95, 105, 92], 1)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    dish_mask = np.full((80, 80), 255, dtype=np.uint8)

    candidate_mask = build_leaf_candidate_mask(image, hsv_image, dish_mask)

    assert candidate_mask[28, 28]
    assert not candidate_mask[55, 40]


def test_auto_settings_uses_latest_similar_reference_json_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image = np.full((40, 40, 3), [40, 80, 40], dtype=np.uint8)
    image_path = tmp_path / "neues_bild_anderer_name.jpg"
    cv2.imwrite(str(image_path), image)
    reference_path = tmp_path / "klein_blass_stoerfleck.jpg"
    cv2.imwrite(str(reference_path), image)

    json_path = tmp_path / "reference_settings.json"
    write_reference_json(
        json_path,
        [
            {
                "image": str(reference_path),
                "settings": reference_settings(
                    h_min=10,
                    h_max=90,
                    s_min=50,
                    s_max=255,
                    v_min=20,
                    v_max=255,
                    min_object_area_px=100,
                    max_object_area_px=50000,
                    green_dominance_margin=5,
                    green_index_min=10,
                    leaf_fill_px=1,
                    pale_leaf_expansion_px=8,
                    root_trim_px=2,
                    inner_dish_percent=80,
                    morphology_kernel_size=3,
                ),
            },
            {
                "image": str(reference_path),
                "settings": reference_settings(
                    h_min=43,
                    h_max=82,
                    s_min=231,
                    s_max=255,
                    v_min=57,
                    v_max=255,
                    min_object_area_px=1454,
                    max_object_area_px=120000,
                    green_dominance_margin=10,
                    green_index_min=46,
                    leaf_fill_px=2,
                    pale_leaf_expansion_px=28,
                    root_trim_px=10,
                    inner_dish_percent=78,
                    morphology_kernel_size=3,
                ),
            },
        ],
    )
    monkeypatch.setattr(auto_settings, "REFERENCE_SETTINGS_JSON", json_path)
    monkeypatch.setattr(auto_settings, "REFERENCE_SETTINGS_DIR", tmp_path)

    settings = suggest_analysis_settings(image_path)

    assert settings.thresholds.h_min == 43
    assert settings.thresholds.s_min == 231
    assert settings.min_object_area_px == 1454
    assert settings.pale_leaf_expansion_px == 28
    assert settings.inner_dish_factor == 0.78


def test_auto_settings_ignores_dissimilar_reference_json_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image = np.full((80, 80, 3), [40, 36, 30], dtype=np.uint8)
    cv2.circle(image, (40, 40), 14, [45, 85, 42], -1)
    image_path = tmp_path / "neues_dunkles_bild.jpg"
    cv2.imwrite(str(image_path), image)

    reference_image = np.full((80, 80, 3), [245, 245, 245], dtype=np.uint8)
    reference_path = tmp_path / "helles_referenzbild.jpg"
    cv2.imwrite(str(reference_path), reference_image)

    json_path = tmp_path / "reference_settings.json"
    write_reference_json(
        json_path,
        [
            {
                "image": str(reference_path),
                "settings": reference_settings(
                    h_min=1,
                    h_max=2,
                    s_min=3,
                    s_max=4,
                    v_min=5,
                    v_max=6,
                    min_object_area_px=7,
                    max_object_area_px=8,
                    green_dominance_margin=9,
                    green_index_min=10,
                    leaf_fill_px=11,
                    pale_leaf_expansion_px=12,
                    root_trim_px=13,
                    inner_dish_percent=14,
                    morphology_kernel_size=15,
                ),
            },
        ],
    )
    monkeypatch.setattr(auto_settings, "REFERENCE_SETTINGS_JSON", json_path)
    monkeypatch.setattr(auto_settings, "REFERENCE_SETTINGS_DIR", tmp_path)

    settings = suggest_analysis_settings(
        image_path,
        manual_petri_circle=(40, 40, 35),
    )

    assert settings.thresholds.h_min != 1
    assert settings.min_object_area_px != 7


def test_reference_settings_reject_implausible_medium_flood() -> None:
    image = np.full((220, 220, 3), [245, 245, 245], dtype=np.uint8)
    cv2.circle(image, (110, 110), 92, [55, 75, 65], -1)
    cv2.circle(image, (110, 110), 92, [190, 190, 190], 3)
    cv2.circle(image, (110, 110), 78, [45, 70, 45], -1)
    cv2.rectangle(image, (20, 80), (85, 190), [35, 120, 35], -1)
    cv2.rectangle(image, (145, 50), (200, 175), [35, 120, 35], -1)

    settings = AnalysisSettings(
        thresholds=HSVThresholds(h_min=30, h_max=120, s_min=20, v_min=20),
        min_object_area_px=0,
        max_object_area_px=120000,
        green_dominance_margin=0,
        green_index_min=-30,
        leaf_fill_px=2,
        pale_leaf_expansion_px=5,
        root_trim_px=0,
        inner_dish_factor=0.86,
    )

    assert not reference_settings_is_plausible_for_image(image, settings)


def test_reference_settings_accept_curated_examples() -> None:
    for reference in auto_settings.load_reference_settings():
        image_path = auto_settings.reference_image_path(reference)
        assert image_path is not None
        image = cv2.imread(str(image_path))
        assert image is not None
        settings = auto_settings.settings_from_reference_entry(reference)

        assert reference_settings_is_plausible_for_image(image, settings)


def reference_settings(**overrides: int) -> dict[str, int]:
    return overrides


def write_reference_json(path: Path, references: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "references": references,
            }
        ),
        encoding="utf-8",
    )
