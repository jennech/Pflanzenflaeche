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


@dataclass(frozen=True)
class HSVThresholds:
    h_min: int = 38
    h_max: int = 92
    s_min: int = 55
    s_max: int = 255
    v_min: int = 35
    v_max: int = 255

    def lower_bound(self) -> np.ndarray:
        return np.array([self.h_min, self.s_min, self.v_min], dtype=np.uint8)

    def upper_bound(self) -> np.ndarray:
        return np.array([self.h_max, self.s_max, self.v_max], dtype=np.uint8)


@dataclass(frozen=True)
class AnalysisResult:
    original_qimage: QImage
    overlay_qimage: QImage
    mask_qimage: QImage
    measurement: MeasurementResult


def analyze_green_area(
    image_path: Path,
    thresholds: Optional[HSVThresholds] = None,
) -> AnalysisResult:
    thresholds = thresholds or HSVThresholds()
    bgr_image = cv2.imread(str(image_path))
    if bgr_image is None:
        raise ValueError(f"Bild konnte nicht geladen werden: {image_path}")

    petri_circle = detect_petri_circle(bgr_image)
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv_image,
        thresholds.lower_bound(),
        thresholds.upper_bound(),
    )

    dish_mask = build_petri_mask(mask.shape, petri_circle, shrink_factor=0.90)
    mask = cv2.bitwise_and(mask, dish_mask)

    kernel = np.ones((3, 3), dtype=np.uint8)
    cleaned_mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)
    cleaned_mask = filter_small_components(cleaned_mask, min_area_px=120)

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
