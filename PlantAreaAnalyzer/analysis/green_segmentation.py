from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtGui import QImage

from analysis.calibration import calibrate_from_petri_diameter_px
from analysis.measurement import MeasurementResult, measure_green_area
from analysis.petri_detection import build_petri_mask, detect_petri_circle
from analysis.overlay import build_green_overlay
from analysis.settings import AnalysisSettings, HSVThresholds


@dataclass(frozen=True)
class AnalysisResult:
    original_qimage: QImage
    overlay_qimage: QImage
    mask_qimage: QImage
    measurement: MeasurementResult


def analyze_green_area(
    image_path: Path,
    thresholds: Optional[HSVThresholds] = None,
    settings: Optional[AnalysisSettings] = None,
) -> AnalysisResult:
    settings = settings or AnalysisSettings(thresholds=thresholds or HSVThresholds())
    bgr_image = cv2.imread(str(image_path))
    if bgr_image is None:
        raise ValueError(f"Bild konnte nicht geladen werden: {image_path}")

    petri_circle = detect_petri_circle(bgr_image)
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

    kernel_size = max(1, settings.morphology_kernel_size)
    kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
    cleaned_mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)
    cleaned_mask = filter_small_components(
        cleaned_mask,
        min_area_px=settings.min_object_area_px,
    )

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
    green_index_mask = excess_green >= settings.green_index_min

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

    return ((green_index_mask & relaxed_hsv_mask).astype(np.uint8)) * 255


def filter_small_components(mask: np.ndarray, min_area_px: int) -> np.ndarray:
    """Remove tiny green islands that are usually noise or color fringes."""

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    filtered = np.zeros_like(mask)

    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        if area >= min_area_px:
            filtered[labels == label] = 255

    return filtered


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
