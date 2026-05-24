from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

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
