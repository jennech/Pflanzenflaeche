import numpy as np

from analysis.green_segmentation import build_pale_leaf_expansion_mask
from analysis.green_segmentation import build_green_index_mask
from analysis.green_segmentation import build_green_dominance_mask
from analysis.green_segmentation import filter_components_by_area
from analysis.green_segmentation import filter_small_components
from analysis.green_segmentation import suppress_root_like_components
from analysis.settings import AnalysisSettings

import cv2


def test_green_dominance_filters_blue_color_fringe() -> None:
    bgr_image = np.array(
        [
            [[20, 90, 20], [90, 95, 20]],
        ],
        dtype=np.uint8,
    )

    mask = build_green_dominance_mask(bgr_image, min_margin=20)

    assert mask[0, 0] == 255
    assert mask[0, 1] == 0


def test_filter_small_components_keeps_only_large_regions() -> None:
    mask = np.zeros((6, 6), dtype=np.uint8)
    mask[0, 0] = 255
    mask[2:5, 2:5] = 255

    filtered = filter_small_components(mask, min_area_px=4)

    assert filtered[0, 0] == 0
    assert filtered[3, 3] == 255


def test_filter_components_by_area_removes_huge_artifacts() -> None:
    mask = np.zeros((20, 20), dtype=np.uint8)
    mask[2:5, 2:5] = 255
    mask[8:20, 8:20] = 255

    filtered = filter_components_by_area(mask, min_area_px=4, max_area_px=80)

    assert filtered[3, 3] == 255
    assert filtered[12, 12] == 0


def test_green_index_detects_dark_desaturated_leaf() -> None:
    bgr_image = np.array(
        [
            [[44, 72, 42], [65, 66, 61]],
        ],
        dtype=np.uint8,
    )
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)

    mask = build_green_index_mask(
        bgr_image,
        hsv_image,
        AnalysisSettings(green_index_min=8),
    )

    assert mask[0, 0] == 255
    assert mask[0, 1] == 0


def test_green_index_still_detects_dark_leaf_with_high_absolute_threshold() -> None:
    bgr_image = np.array(
        [
            [[44, 72, 42], [90, 76, 48]],
        ],
        dtype=np.uint8,
    )
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)

    mask = build_green_index_mask(
        bgr_image,
        hsv_image,
        AnalysisSettings(green_index_min=80),
    )

    assert mask[0, 0] == 255
    assert mask[0, 1] == 0


def test_pale_leaf_expansion_only_adds_pixels_near_green_seed() -> None:
    bgr_image = np.full((5, 8, 3), [90, 76, 48], dtype=np.uint8)
    bgr_image[2, 1] = [35, 95, 35]
    bgr_image[1:4, 2:5] = [170, 185, 168]
    bgr_image[1:4, 6:8] = [170, 185, 168]
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    seed_mask = np.zeros((5, 8), dtype=np.uint8)
    seed_mask[2, 1] = 255

    mask = build_pale_leaf_expansion_mask(
        bgr_image,
        hsv_image,
        seed_mask,
        expansion_px=3,
    )

    assert mask[2, 3] == 255
    assert mask[2, 7] == 0


def test_root_like_pale_components_are_removed() -> None:
    mask = np.zeros((12, 20), dtype=np.uint8)
    mask[2, 2:16] = 255
    mask[7:10, 4:8] = 255

    filtered = suppress_root_like_components(mask)

    assert filtered[2, 8] == 0
    assert filtered[8, 6] == 255


def test_pale_leaf_expansion_can_be_disabled() -> None:
    bgr_image = np.array([[[35, 95, 35], [170, 185, 168]]], dtype=np.uint8)
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    seed_mask = np.array([[255, 0]], dtype=np.uint8)

    mask = build_pale_leaf_expansion_mask(
        bgr_image,
        hsv_image,
        seed_mask,
        expansion_px=0,
    )

    assert not np.any(mask)
