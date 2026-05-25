from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtGui import QImage

from analysis.calibration import calibrate_from_petri_diameter_px
from analysis.measurement import MeasurementResult, measure_green_area
from analysis.petri_detection import PetriCircle, build_petri_mask, detect_petri_circle
from analysis.overlay import build_green_overlay
from analysis.settings import AnalysisSettings, HSVThresholds


@dataclass(frozen=True)
class AnalysisResult:
    original_qimage: QImage
    overlay_qimage: QImage
    mask_qimage: QImage
    measurement: MeasurementResult
    petri_circle: PetriCircle


def analyze_green_area(
    image_path: Path,
    thresholds: Optional[HSVThresholds] = None,
    settings: Optional[AnalysisSettings] = None,
) -> AnalysisResult:
    settings = settings or AnalysisSettings(thresholds=thresholds or HSVThresholds())
    bgr_image = cv2.imread(str(image_path))
    if bgr_image is None:
        raise ValueError(f"Bild konnte nicht geladen werden: {image_path}")

    petri_circle = (
        PetriCircle(*settings.manual_petri_circle)
        if settings.manual_petri_circle is not None
        else detect_petri_circle(bgr_image)
    )
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
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
    index_mask = build_green_index_mask(
        bgr_image,
        hsv_image,
        settings,
    )
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
        settings,
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
    cleaned_mask = suppress_thin_protrusions(cleaned_mask, settings.root_trim_px)
    cleaned_mask = remove_components_at_points(
        cleaned_mask,
        settings.excluded_component_points,
    )
    cleaned_mask = add_leaf_area_at_points(
        cleaned_mask,
        settings.manual_leaf_points,
        settings.manual_leaf_radius_px,
        settings.manual_leaf_patches,
    )
    cleaned_mask = cv2.bitwise_and(cleaned_mask, dish_mask)

    calibration = calibrate_from_petri_diameter_px(
        pixel_diameter=float(petri_circle.radius * 2),
    )
    measurement = measure_green_area(cleaned_mask, calibration)

    original_rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    overlay_rgb = build_green_overlay(original_rgb, cleaned_mask)
    mask_rgb = cv2.cvtColor(cleaned_mask, cv2.COLOR_GRAY2RGB)

    return AnalysisResult(
        original_qimage=numpy_to_qimage(original_rgb),
        overlay_qimage=numpy_to_qimage(overlay_rgb),
        mask_qimage=numpy_to_qimage(mask_rgb),
        measurement=measurement,
        petri_circle=petri_circle,
    )


def build_green_dominance_mask(
    bgr_image: np.ndarray,
    min_margin: int,
) -> np.ndarray:
    """Keep pixels where green is stronger than red and blue."""

    blue, green, red = cv2.split(bgr_image.astype(np.int16))
    green_dominates = (
        (green - red >= min_margin)
        & (green - blue >= min_margin)
    )
    return (green_dominates.astype(np.uint8)) * 255


def build_green_index_mask(
    bgr_image: np.ndarray,
    hsv_image: np.ndarray,
    settings: AnalysisSettings,
) -> np.ndarray:
    """Detect dark or desaturated leaves with an Excess Green color index."""

    blue, green, red = cv2.split(bgr_image.astype(np.int16))
    excess_green = (2 * green) - red - blue

    intensity = red + green + blue
    normalized_excess_green = np.divide(
        excess_green,
        np.maximum(intensity, 1),
        dtype=np.float32,
    )
    normalized_threshold = max(0.06, settings.green_index_min / 1000.0)
    green_index_mask = (
        (excess_green >= settings.green_index_min)
        | (normalized_excess_green >= normalized_threshold)
    )
    index_margin = int(np.clip(settings.green_dominance_margin - 10, -12, 12))
    green_not_below_other_channels = (
        (green - red >= index_margin)
        & (green - blue >= index_margin)
    )

    h_min = max(0, settings.thresholds.h_min - 18)
    h_max = min(179, settings.thresholds.h_max + 18)
    s_min = max(10, settings.thresholds.s_min - 45)
    v_min = max(10, settings.thresholds.v_min - 25)

    hue = hsv_image[:, :, 0]
    saturation = hsv_image[:, :, 1]
    value = hsv_image[:, :, 2]
    relaxed_hsv_mask = (
        (hue >= h_min)
        & (hue <= h_max)
        & (saturation >= s_min)
        & (value >= v_min)
    )

    return (
        (
            green_index_mask
            & green_not_below_other_channels
            & relaxed_hsv_mask
        ).astype(np.uint8)
    ) * 255


def build_pale_leaf_expansion_mask(
    bgr_image: np.ndarray,
    hsv_image: np.ndarray,
    seed_mask: np.ndarray,
    expansion_px: int,
    settings: AnalysisSettings | None = None,
) -> np.ndarray:
    """Add pale tissue only near already detected green plant pixels.

    White or chlorotic leaves are ambiguous in petri images, because agar,
    reflections, and medium can be similarly bright. Restricting detection to
    a small neighborhood around green seeds avoids turning the whole dish into
    plant area while recovering pale leaf margins.
    """

    if expansion_px <= 0 or not np.any(seed_mask):
        return np.zeros_like(seed_mask)

    kernel_size = (expansion_px * 2) + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )
    nearby_seed = cv2.dilate(seed_mask, kernel)

    blue, green, red = cv2.split(bgr_image.astype(np.int16))
    hue = hsv_image[:, :, 0]
    saturation = hsv_image[:, :, 1]
    value = hsv_image[:, :, 2]
    saturation_limit = 145 if expansion_px >= 22 else 115
    channel_tolerance = 18 if expansion_px >= 22 else 12

    faint_green_or_pale = (
        (green >= red - channel_tolerance)
        & (green >= blue - channel_tolerance)
        & (hue >= 20)
        & (hue <= 115)
        & (saturation <= saturation_limit)
        & (value >= 45)
        & (value <= 235)
    )
    pale_low_saturation = (
        (saturation <= 55)
        & (value >= 80)
        & (value <= 220)
        & (green >= red - 20)
        & (green >= blue - 20)
    )
    candidate_mask = faint_green_or_pale | pale_low_saturation
    if settings is not None:
        candidate_mask &= build_expansion_green_gate(
            bgr_image,
            settings.green_dominance_margin,
            settings.green_index_min,
        )

    candidate = candidate_mask.astype(np.uint8) * 255
    pale_mask = cv2.bitwise_and(candidate, nearby_seed)
    seeded_mask = keep_seeded_leaf_expansion_components(
        pale_mask,
        seed_mask,
        expansion_px,
    )
    return suppress_root_like_components(seeded_mask)


def build_expansion_green_gate(
    bgr_image: np.ndarray,
    green_dominance_margin: int,
    green_index_min: int,
) -> np.ndarray:
    """Make pale expansion obey the same strictness sliders as the green seed."""

    blue, green, red = cv2.split(bgr_image.astype(np.int16))
    excess_green = (2 * green) - red - blue
    intensity = red + green + blue
    normalized_excess_green = np.divide(
        excess_green,
        np.maximum(intensity, 1),
        dtype=np.float32,
    )

    channel_margin = int(np.clip(green_dominance_margin - 18, -22, 8))
    excess_threshold = int(np.clip(green_index_min // 3, -12, 28))
    normalized_threshold = float(np.clip(green_index_min / 1400.0, -0.02, 0.055))

    return (
        (green - red >= channel_margin)
        & (green - blue >= channel_margin)
        & (
            (excess_green >= excess_threshold)
            | (normalized_excess_green >= normalized_threshold)
        )
    )


def keep_seeded_leaf_expansion_components(
    expansion_mask: np.ndarray,
    seed_mask: np.ndarray,
    expansion_px: int,
) -> np.ndarray:
    """Keep pale additions that are plausibly attached to real leaf seeds."""

    if not np.any(expansion_mask):
        return expansion_mask

    contact_radius = max(2, min(10, expansion_px // 3))
    contact_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        ((contact_radius * 2) + 1, (contact_radius * 2) + 1),
    )
    seed_contact = cv2.dilate(seed_mask, contact_kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(expansion_mask, 8)
    filtered = np.zeros_like(expansion_mask)

    for label in range(1, num_labels):
        component = labels == label
        touches_seed = np.any(seed_contact[component] > 0)
        if not touches_seed:
            continue

        area = stats[label, cv2.CC_STAT_AREA]
        if area < 4:
            continue

        if is_root_like_component(stats[label]):
            continue

        filtered[component] = 255

    return filtered


def suppress_root_like_components(mask: np.ndarray) -> np.ndarray:
    """Remove thin, elongated pale structures that are likely roots."""

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    filtered = np.zeros_like(mask)

    for label in range(1, num_labels):
        if is_root_like_component(stats[label]):
            continue

        filtered[labels == label] = 255

    return filtered


def is_root_like_component(stats_row: np.ndarray) -> bool:
    area = stats_row[cv2.CC_STAT_AREA]
    width = stats_row[cv2.CC_STAT_WIDTH]
    height = stats_row[cv2.CC_STAT_HEIGHT]
    short_side = max(1, min(width, height))
    long_side = max(width, height)
    aspect_ratio = long_side / short_side
    fill_ratio = area / max(1, width * height)

    if aspect_ratio >= 4.5 and fill_ratio <= 0.45:
        return True
    if short_side <= 2 and long_side >= 8:
        return True
    if area < 220 and aspect_ratio >= 3.0 and fill_ratio <= 0.35:
        return True
    return False


def fill_leaf_gaps(mask: np.ndarray, fill_px: int) -> np.ndarray:
    """Close gaps and fill enclosed leaf interiors without broad expansion."""

    if fill_px <= 0:
        return mask

    kernel_size = (fill_px * 2) + 1
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )
    filled = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    hole_area_limit = max(80, fill_px * fill_px * 220)
    filled = fill_enclosed_holes(filled, max_hole_area_px=hole_area_limit)
    return cv2.bitwise_or(mask, filled)


def fill_enclosed_holes(mask: np.ndarray, max_hole_area_px: int) -> np.ndarray:
    """Fill fully enclosed holes, such as leaf centers missed by color thresholds."""

    inverted = cv2.bitwise_not(mask)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(inverted, 8)
    if num_labels <= 1:
        return mask

    height, width = mask.shape
    filled = mask.copy()
    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area > max_hole_area_px:
            continue

        left = stats[label, cv2.CC_STAT_LEFT]
        top = stats[label, cv2.CC_STAT_TOP]
        component_width = stats[label, cv2.CC_STAT_WIDTH]
        component_height = stats[label, cv2.CC_STAT_HEIGHT]
        touches_border = (
            left == 0
            or top == 0
            or left + component_width >= width
            or top + component_height >= height
        )
        if touches_border:
            continue

        filled[labels == label] = 255

    return filled


def suppress_thin_protrusions(mask: np.ndarray, root_trim_px: int = 4) -> np.ndarray:
    """Trim narrow root-like appendages while preserving compact leaf regions."""

    if not np.any(mask):
        return mask

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    if not np.any(opened):
        return mask

    opened = trim_long_appendages(opened, root_trim_px)
    opened = fill_enclosed_holes(opened, max_hole_area_px=1200)
    return cv2.bitwise_or(opened, keep_compact_leaf_components(mask, opened))


def trim_long_appendages(mask: np.ndarray, root_trim_px: int = 4) -> np.ndarray:
    """Keep component cores and nearby lobes, but drop long thin attached tails."""

    if root_trim_px <= 0:
        return mask

    trim_strength = max(1, root_trim_px)
    core_distance_px = 2.8 + (trim_strength * 0.3)
    regrow_radius_px = max(4, 10 - trim_strength)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    trimmed = np.zeros_like(mask)

    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        component = (labels == label).astype(np.uint8) * 255
        if area < 180:
            trimmed[component > 0] = 255
            continue

        distance = cv2.distanceTransform(component, cv2.DIST_L2, 5)
        core = (distance >= core_distance_px).astype(np.uint8) * 255
        if not np.any(core):
            if is_compact_component(stats[label]):
                trimmed[component > 0] = 255
            continue

        # Re-grow from the thick core only a limited distance. Leaf lobes return,
        # long root-like hooks stay outside.
        kernel_size = (regrow_radius_px * 2) + 1
        regrow_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (kernel_size, kernel_size),
        )
        regrown = cv2.dilate(core, regrow_kernel)
        regrown = cv2.bitwise_and(regrown, component)
        trimmed[regrown > 0] = 255

    return trimmed


def keep_compact_leaf_components(mask: np.ndarray, core_mask: np.ndarray) -> np.ndarray:
    """Restore compact components that opening would otherwise erase."""

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    restored = np.zeros_like(mask)
    for label in range(1, num_labels):
        component = labels == label
        if np.any(core_mask[component] > 0):
            continue

        if is_compact_component(stats[label], min_area=80):
            restored[component] = 255

    return restored


def is_compact_component(stats_row: np.ndarray, min_area: int = 80) -> bool:
    area = stats_row[cv2.CC_STAT_AREA]
    width = stats_row[cv2.CC_STAT_WIDTH]
    height = stats_row[cv2.CC_STAT_HEIGHT]
    short_side = max(1, min(width, height))
    long_side = max(width, height)
    fill_ratio = area / max(1, width * height)
    return bool(area >= min_area and long_side / short_side <= 2.8 and fill_ratio >= 0.35)


def filter_small_components(mask: np.ndarray, min_area_px: int) -> np.ndarray:
    """Remove tiny green islands that are usually noise or color fringes."""

    return filter_components_by_area(mask, min_area_px=min_area_px)


def filter_components_by_area(
    mask: np.ndarray,
    min_area_px: int,
    max_area_px: int = 0,
) -> np.ndarray:
    """Remove implausibly small noise and optionally huge merged artifacts."""

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    filtered = np.zeros_like(mask)

    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area < min_area_px:
            continue
        if max_area_px > 0 and area > max_area_px:
            continue

        filtered[labels == label] = 255

    return filtered


def remove_components_at_points(
    mask: np.ndarray,
    points: tuple[tuple[int, int], ...],
    search_radius_px: int = 16,
) -> np.ndarray:
    """Remove complete components touched, or nearly touched, by exclusion clicks."""

    if not points:
        return mask

    num_labels, labels, _, _ = cv2.connectedComponentsWithStats(mask, 8)
    if num_labels <= 1:
        return mask

    height, width = mask.shape
    labels_to_remove: set[int] = set()
    for point_x, point_y in points:
        if point_x < 0 or point_y < 0 or point_x >= width or point_y >= height:
            continue

        label = nearest_component_label(
            labels,
            point_x,
            point_y,
            search_radius_px,
        )
        if label > 0:
            labels_to_remove.add(label)

    if not labels_to_remove:
        return mask

    filtered = mask.copy()
    for label in labels_to_remove:
        filtered[labels == label] = 0
    return filtered


def add_leaf_area_at_points(
    mask: np.ndarray,
    points: tuple[tuple[int, int], ...],
    radius_px: int = 14,
    patches: tuple[tuple[int, int, int], ...] = (),
) -> np.ndarray:
    """Add small manual leaf-area patches around clicked points."""

    if not points and not patches:
        return mask

    height, width = mask.shape
    corrected = mask.copy()
    radius = max(1, int(radius_px))
    for point_x, point_y in points:
        if point_x < 0 or point_y < 0 or point_x >= width or point_y >= height:
            continue

        cv2.circle(corrected, (point_x, point_y), radius, 255, -1)

    for point_x, point_y, patch_radius_px in patches:
        if point_x < 0 or point_y < 0 or point_x >= width or point_y >= height:
            continue

        patch_radius = max(1, int(patch_radius_px))
        cv2.circle(corrected, (point_x, point_y), patch_radius, 255, -1)

    return corrected


def nearest_component_label(
    labels: np.ndarray,
    point_x: int,
    point_y: int,
    search_radius_px: int,
) -> int:
    """Find the clicked label or the nearest label within a small radius."""

    direct_label = int(labels[point_y, point_x])
    if direct_label > 0:
        return direct_label

    radius = max(0, search_radius_px)
    if radius == 0:
        return 0

    height, width = labels.shape
    x_min = max(0, point_x - radius)
    x_max = min(width, point_x + radius + 1)
    y_min = max(0, point_y - radius)
    y_max = min(height, point_y + radius + 1)
    window = labels[y_min:y_max, x_min:x_max]
    candidate_positions = np.argwhere(window > 0)
    if candidate_positions.size == 0:
        return 0

    absolute_y = candidate_positions[:, 0] + y_min
    absolute_x = candidate_positions[:, 1] + x_min
    distances = (absolute_x - point_x) ** 2 + (absolute_y - point_y) ** 2
    nearest_index = int(np.argmin(distances))
    return int(window[tuple(candidate_positions[nearest_index])])


def numpy_to_qimage(rgb_image: np.ndarray) -> QImage:
    height, width, channels = rgb_image.shape
    bytes_per_line = channels * width
    return QImage(
        rgb_image.data,
        width,
        height,
        bytes_per_line,
        QImage.Format_RGB888,
    ).copy()
