from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from analysis.green_segmentation import build_green_dominance_mask
from analysis.green_segmentation import build_green_index_mask
from analysis.green_segmentation import build_pale_leaf_expansion_mask
from analysis.green_segmentation import fill_leaf_gaps
from analysis.green_segmentation import filter_components_by_area
from analysis.green_segmentation import suppress_thin_protrusions
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
        s_min=clamp_int(percentile(saturation, 8) - 20, 18, 210),
        s_max=255,
        v_min=clamp_int(percentile(value, 5) - 20, 20, 180),
        v_max=255,
    )

    min_area = max(80, int(candidate_mask.sum() * 0.003))
    max_area = max(6000, int(candidate_mask.sum() * 0.65))
    data_driven_settings = AnalysisSettings(
        thresholds=thresholds,
        min_object_area_px=min(min_area, 2500),
        max_object_area_px=min(max_area, 120000),
        green_dominance_margin=clamp_int(percentile(green_margin, 20) - 6, 4, 45),
        green_index_min=clamp_int(percentile(excess_green, 25) - 8, -20, 80),
        leaf_fill_px=3,
        pale_leaf_expansion_px=8,
        root_trim_px=base_settings.root_trim_px,
        inner_dish_factor=base_settings.inner_dish_factor,
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )
    return choose_best_settings(
        bgr_image=bgr_image,
        hsv_image=hsv_image,
        petri_circle=petri_circle,
        base_settings=base_settings,
        candidate_settings=[
            base_settings,
            stricter_root_variant(base_settings, manual_petri_circle),
            data_driven_settings,
            dark_leaf_high_saturation_settings(base_settings, manual_petri_circle),
            root_strict_settings(base_settings, manual_petri_circle),
            pale_leaf_settings(base_settings, manual_petri_circle),
            pale_leaf_base_root_settings(base_settings, manual_petri_circle),
        ],
    )


def choose_best_settings(
    bgr_image: np.ndarray,
    hsv_image: np.ndarray,
    petri_circle: PetriCircle,
    base_settings: AnalysisSettings,
    candidate_settings: list[AnalysisSettings],
) -> AnalysisSettings:
    scored_settings: list[tuple[float, AnalysisSettings]] = []
    for settings in candidate_settings:
        mask = build_mask_for_scoring(bgr_image, hsv_image, petri_circle, settings)
        scored_settings.append((score_mask(mask, petri_circle), settings))

    if not scored_settings:
        return conservative_dark_leaf_settings(base_settings)

    return max(scored_settings, key=lambda entry: entry[0])[1]


def build_mask_for_scoring(
    bgr_image: np.ndarray,
    hsv_image: np.ndarray,
    petri_circle: PetriCircle,
    settings: AnalysisSettings,
) -> np.ndarray:
    hsv_mask = cv2.inRange(
        hsv_image,
        settings.thresholds.lower_bound(),
        settings.thresholds.upper_bound(),
    )
    dominance_mask = build_green_dominance_mask(
        bgr_image,
        settings.green_dominance_margin,
    )
    strict_mask = cv2.bitwise_and(hsv_mask, dominance_mask)
    index_mask = build_green_index_mask(bgr_image, hsv_image, settings)
    mask = cv2.bitwise_or(strict_mask, index_mask)
    dish_mask = build_petri_mask(
        mask.shape,
        petri_circle,
        shrink_factor=settings.inner_dish_factor,
    )
    mask = cv2.bitwise_and(mask, dish_mask)
    pale_leaf_mask = build_pale_leaf_expansion_mask(
        bgr_image,
        hsv_image,
        mask,
        settings.pale_leaf_expansion_px,
    )
    mask = cv2.bitwise_or(mask, cv2.bitwise_and(pale_leaf_mask, dish_mask))
    mask = fill_leaf_gaps(mask, settings.leaf_fill_px)

    kernel_size = max(1, settings.morphology_kernel_size)
    kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
    cleaned_mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)
    cleaned_mask = filter_components_by_area(
        cleaned_mask,
        min_area_px=settings.min_object_area_px,
        max_area_px=settings.max_object_area_px,
    )
    return suppress_thin_protrusions(cleaned_mask, settings.root_trim_px)


def score_mask(mask: np.ndarray, petri_circle: PetriCircle) -> float:
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if num_labels <= 1:
        return -1_000_000.0

    component_scores: list[float] = []
    total_area = 0
    thin_penalty = 0.0
    edge_penalty = 0.0
    for label in range(1, num_labels):
        area = int(stats[label, cv2.CC_STAT_AREA])
        width = int(stats[label, cv2.CC_STAT_WIDTH])
        height = int(stats[label, cv2.CC_STAT_HEIGHT])
        if area <= 0:
            continue

        total_area += area
        short_side = max(1, min(width, height))
        long_side = max(width, height)
        aspect_ratio = long_side / short_side
        fill_ratio = area / max(1, width * height)
        component_score = min(area, 20_000) * min(1.0, fill_ratio + 0.25)
        if aspect_ratio > 3.5:
            thin_penalty += area * (aspect_ratio - 3.5)
        if touches_analysis_edge(labels == label, petri_circle):
            edge_penalty += area * 1.5
        component_scores.append(component_score)

    if total_area == 0:
        return -1_000_000.0

    dish_area = np.pi * petri_circle.radius * petri_circle.radius
    coverage = total_area / max(1.0, dish_area)
    plausible_area_score = total_area
    if coverage < 0.015:
        plausible_area_score -= (0.015 - coverage) * dish_area * 8.0
    if coverage > 0.23:
        plausible_area_score -= (coverage - 0.23) * dish_area * 5.0

    large_components = sum(1 for score in component_scores if score > 300)
    plant_count_score = 5000.0 - abs(large_components - 4) * 1200.0
    return plausible_area_score + plant_count_score - thin_penalty - edge_penalty


def touches_analysis_edge(component: np.ndarray, petri_circle: PetriCircle) -> bool:
    y_coords, x_coords = np.nonzero(component)
    if y_coords.size == 0:
        return False

    distances = np.hypot(x_coords - petri_circle.center_x, y_coords - petri_circle.center_y)
    return bool(np.any(distances > petri_circle.radius * 0.84))


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
        root_trim_px=base_settings.root_trim_px,
        inner_dish_factor=base_settings.inner_dish_factor,
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=base_settings.manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def stricter_root_variant(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    thresholds = base_settings.thresholds
    return AnalysisSettings(
        thresholds=HSVThresholds(
            h_min=thresholds.h_min,
            h_max=min(thresholds.h_max, 120),
            s_min=clamp_int(max(thresholds.s_min, 165), 0, 255),
            s_max=thresholds.s_max,
            v_min=thresholds.v_min,
            v_max=thresholds.v_max,
        ),
        min_object_area_px=max(base_settings.min_object_area_px, 300),
        max_object_area_px=min(base_settings.max_object_area_px, 50000),
        green_dominance_margin=max(base_settings.green_dominance_margin, 22),
        green_index_min=max(base_settings.green_index_min, 80),
        leaf_fill_px=min(base_settings.leaf_fill_px, 3),
        pale_leaf_expansion_px=min(base_settings.pale_leaf_expansion_px, 14),
        root_trim_px=max(base_settings.root_trim_px, 6),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.86),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def dark_leaf_high_saturation_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=30, h_max=120, s_min=165, s_max=255, v_min=20),
        min_object_area_px=300,
        max_object_area_px=75000,
        green_dominance_margin=17,
        green_index_min=80,
        leaf_fill_px=2,
        pale_leaf_expansion_px=30,
        root_trim_px=max(base_settings.root_trim_px, 4),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.88),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def root_strict_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=30, h_max=112, s_min=185, s_max=255, v_min=25),
        min_object_area_px=350,
        max_object_area_px=45000,
        green_dominance_margin=24,
        green_index_min=80,
        leaf_fill_px=2,
        pale_leaf_expansion_px=14,
        root_trim_px=7,
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.86),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def pale_leaf_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=25, h_max=120, s_min=85, s_max=255, v_min=25),
        min_object_area_px=240,
        max_object_area_px=65000,
        green_dominance_margin=12,
        green_index_min=45,
        leaf_fill_px=4,
        pale_leaf_expansion_px=22,
        root_trim_px=max(base_settings.root_trim_px, 3),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.86),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def pale_leaf_base_root_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    """Recover grey-green leaf bases while keeping root-like appendages constrained."""
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=22, h_max=125, s_min=38, s_max=255, v_min=20),
        min_object_area_px=160,
        max_object_area_px=70000,
        green_dominance_margin=0,
        green_index_min=-5,
        leaf_fill_px=1,
        pale_leaf_expansion_px=32,
        root_trim_px=max(base_settings.root_trim_px, 8),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.86),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def percentile(values: np.ndarray, percent: float) -> float:
    return float(np.percentile(values, percent))


def clamp_int(value: float, minimum: int, maximum: int) -> int:
    return int(max(minimum, min(maximum, round(value))))
