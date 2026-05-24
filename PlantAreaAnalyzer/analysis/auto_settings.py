from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from analysis.petri_detection import PetriCircle
from analysis.petri_detection import build_petri_mask
from analysis.petri_detection import detect_petri_circle
from analysis.settings import AnalysisSettings
from analysis.settings import HSVThresholds


def suggest_analysis_settings(
    image_path: Path,
    base_settings: AnalysisSettings | None = None,
    manual_petri_circle: tuple[int, int, int] | None = None,
) -> AnalysisSettings:
    """Derive conservative segmentation defaults from the current image."""

    base_settings = base_settings or AnalysisSettings()
    bgr_image = cv2.imread(str(image_path))
    if bgr_image is None:
        raise ValueError(f"Bild konnte nicht geladen werden: {image_path}")

    petri_circle = (
        PetriCircle(*manual_petri_circle)
        if manual_petri_circle is not None
        else detect_petri_circle(bgr_image)
    )
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    dish_mask = build_petri_mask(
        hsv_image.shape[:2],
        petri_circle,
        shrink_factor=min(base_settings.inner_dish_factor, 0.88),
    )
    candidate_mask = build_leaf_candidate_mask(bgr_image, hsv_image, dish_mask)

    if not np.any(candidate_mask):
        return conservative_dark_leaf_settings(base_settings)

    hue = hsv_image[:, :, 0][candidate_mask]
    saturation = hsv_image[:, :, 1][candidate_mask]
    value = hsv_image[:, :, 2][candidate_mask]
    blue, green, red = cv2.split(bgr_image.astype(np.int16))
    excess_green = ((2 * green) - red - blue)[candidate_mask]
    green_margin = np.minimum(green - red, green - blue)[candidate_mask]

    thresholds = HSVThresholds(
        h_min=clamp_int(percentile(hue, 5) - 12, 0, 179),
        h_max=clamp_int(percentile(hue, 95) + 12, 0, 179),
        s_min=clamp_int(percentile(saturation, 8) - 35, 18, 150),
        s_max=255,
        v_min=clamp_int(percentile(value, 5) - 20, 20, 180),
        v_max=255,
    )

    min_area = max(80, int(candidate_mask.sum() * 0.003))
    max_area = max(6000, int(candidate_mask.sum() * 0.65))
    return AnalysisSettings(
        thresholds=thresholds,
        min_object_area_px=min(min_area, 2500),
        max_object_area_px=min(max_area, 120000),
        green_dominance_margin=clamp_int(percentile(green_margin, 20) - 6, 4, 45),
        green_index_min=clamp_int(percentile(excess_green, 25) - 8, -20, 60),
        leaf_fill_px=3,
        pale_leaf_expansion_px=8,
        inner_dish_factor=base_settings.inner_dish_factor,
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def build_leaf_candidate_mask(
    bgr_image: np.ndarray,
    hsv_image: np.ndarray,
    dish_mask: np.ndarray,
) -> np.ndarray:
    blue, green, red = cv2.split(bgr_image.astype(np.int16))
    hue = hsv_image[:, :, 0]
    saturation = hsv_image[:, :, 1]
    value = hsv_image[:, :, 2]
    intensity = red + green + blue
    excess_green = (2 * green) - red - blue
    normalized_excess = excess_green / np.maximum(intensity, 1)

    dish_pixels = dish_mask > 0
    leaf_like = (
        dish_pixels
        & (hue >= 25)
        & (hue <= 115)
        & (saturation >= 18)
        & (value >= 25)
        & (value <= 245)
        & (green >= red - 8)
        & (green >= blue - 12)
        & ((excess_green >= 4) | (normalized_excess >= 0.035))
    )

    raw_mask = leaf_like.astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel)
    return keep_plausible_candidate_components(cleaned)


def keep_plausible_candidate_components(mask: np.ndarray) -> np.ndarray:
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    filtered = np.zeros_like(mask)

    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        width = stats[label, cv2.CC_STAT_WIDTH]
        height = stats[label, cv2.CC_STAT_HEIGHT]
        if area < 30:
            continue

        short_side = max(1, min(width, height))
        long_side = max(width, height)
        aspect_ratio = long_side / short_side
        fill_ratio = area / max(1, width * height)
        if aspect_ratio > 5.5 and fill_ratio < 0.45:
            continue

        filtered[labels == label] = 1

    return filtered.astype(bool)


def conservative_dark_leaf_settings(base_settings: AnalysisSettings) -> AnalysisSettings:
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=30, h_max=115, s_min=45, s_max=255, v_min=25),
        min_object_area_px=180,
        max_object_area_px=50000,
        green_dominance_margin=14,
        green_index_min=10,
        leaf_fill_px=3,
        pale_leaf_expansion_px=6,
        inner_dish_factor=base_settings.inner_dish_factor,
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=base_settings.manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def percentile(values: np.ndarray, percent: float) -> float:
    return float(np.percentile(values, percent))


def clamp_int(value: float, minimum: int, maximum: int) -> int:
    return int(max(minimum, min(maximum, round(value))))
