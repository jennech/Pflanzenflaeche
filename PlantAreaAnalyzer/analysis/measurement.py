from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from analysis.calibration import CalibrationResult


@dataclass(frozen=True)
class MeasurementResult:
    green_pixels: int
    green_area_mm2: float
    petri_area_mm2: float
    coverage_percent: float


def measure_green_area(
    mask: np.ndarray,
    calibration: CalibrationResult,
) -> MeasurementResult:
    green_pixels = int(np.count_nonzero(mask))
    pixel_area_mm2 = calibration.mm_per_pixel ** 2
    green_area_mm2 = green_pixels * pixel_area_mm2
    coverage_percent = 0.0

    if calibration.petri_area_mm2 > 0:
        coverage_percent = (green_area_mm2 / calibration.petri_area_mm2) * 100.0

    return MeasurementResult(
        green_pixels=green_pixels,
        green_area_mm2=green_area_mm2,
        petri_area_mm2=calibration.petri_area_mm2,
        coverage_percent=coverage_percent,
    )
