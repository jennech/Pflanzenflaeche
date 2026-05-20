from __future__ import annotations

from dataclasses import dataclass
import math


DEFAULT_PETRI_DIAMETER_MM = 55.0


@dataclass(frozen=True)
class CalibrationResult:
    petri_diameter_mm: float
    pixel_diameter: float
    mm_per_pixel: float
    petri_area_mm2: float


def estimate_petri_diameter_px(image_width: int, image_height: int) -> float:
    """Placeholder calibration for the MVP.

    We assume the dish nearly fills the smaller image dimension.
    """

    return float(min(image_width, image_height))


def calibrate_from_image_size(
    image_width: int,
    image_height: int,
    petri_diameter_mm: float = DEFAULT_PETRI_DIAMETER_MM,
) -> CalibrationResult:
    pixel_diameter = estimate_petri_diameter_px(image_width, image_height)
    return calibrate_from_petri_diameter_px(pixel_diameter, petri_diameter_mm)


def calibrate_from_petri_diameter_px(
    pixel_diameter: float,
    petri_diameter_mm: float = DEFAULT_PETRI_DIAMETER_MM,
) -> CalibrationResult:
    if pixel_diameter <= 0:
        raise ValueError("Ungueltige Bildgroesse fuer die Kalibrierung.")

    mm_per_pixel = petri_diameter_mm / pixel_diameter
    petri_area_mm2 = math.pi * (petri_diameter_mm / 2.0) ** 2

    return CalibrationResult(
        petri_diameter_mm=petri_diameter_mm,
        pixel_diameter=pixel_diameter,
        mm_per_pixel=mm_per_pixel,
        petri_area_mm2=petri_area_mm2,
    )
