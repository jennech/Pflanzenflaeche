from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

import analysis.auto_settings as auto_settings
from analysis.auto_settings import build_leaf_candidate_mask
from analysis.auto_settings import suggest_analysis_settings


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


def test_auto_settings_uses_latest_similar_example_csv_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    image = np.full((40, 40, 3), [40, 80, 40], dtype=np.uint8)
    image_path = tmp_path / "neues_bild_anderer_name.jpg"
    cv2.imwrite(str(image_path), image)
    reference_path = tmp_path / "klein_blass_stoerfleck.jpg"
    cv2.imwrite(str(reference_path), image)

    csv_path = tmp_path / "examples.csv"
    csv_path.write_text(
        "\n".join(
            [
                (
                    "image_path,original_filename,h_min,h_max,s_min,s_max,v_min,v_max,"
                    "min_object_area_px,max_object_area_px,green_dominance_margin,"
                    "green_index_min,leaf_fill_px,pale_leaf_expansion_px,"
                    "root_trim_px,inner_dish_percent,morphology_kernel_size"
                ),
                (
                    f"{reference_path},klein_blass_stoerfleck.jpg,10,90,50,255,20,255,"
                    "100,50000,5,10,1,8,2,80,3"
                ),
                (
                    f"{reference_path},klein_blass_stoerfleck.jpg,43,82,231,255,57,255,"
                    "1454,120000,10,46,2,28,10,78,3"
                ),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(auto_settings, "EXAMPLE_SETTINGS_CSV", csv_path)

    settings = suggest_analysis_settings(image_path)

    assert settings.thresholds.h_min == 43
    assert settings.thresholds.s_min == 231
    assert settings.min_object_area_px == 1454
    assert settings.pale_leaf_expansion_px == 28
    assert settings.inner_dish_factor == 0.78


def test_auto_settings_ignores_dissimilar_example_csv_row(
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

    csv_path = tmp_path / "examples.csv"
    csv_path.write_text(
        "\n".join(
            [
                (
                    "image_path,original_filename,h_min,h_max,s_min,s_max,v_min,v_max,"
                    "min_object_area_px,max_object_area_px,green_dominance_margin,"
                    "green_index_min,leaf_fill_px,pale_leaf_expansion_px,"
                    "root_trim_px,inner_dish_percent,morphology_kernel_size"
                ),
                (
                    f"{reference_path},helles_referenzbild.jpg,1,2,3,4,5,6,"
                    "7,8,9,10,11,12,13,14,15"
                ),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(auto_settings, "EXAMPLE_SETTINGS_CSV", csv_path)

    settings = suggest_analysis_settings(
        image_path,
        manual_petri_circle=(40, 40, 35),
    )

    assert settings.thresholds.h_min != 1
    assert settings.min_object_area_px != 7
