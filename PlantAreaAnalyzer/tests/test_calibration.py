import math

from analysis.calibration import calibrate_from_image_size
from analysis.calibration import calibrate_from_petri_diameter_px


def test_calibration_uses_smaller_image_dimension() -> None:
    result = calibrate_from_image_size(800, 600)

    assert result.pixel_diameter == 600.0
    assert math.isclose(result.mm_per_pixel, 55.0 / 600.0)


def test_calibration_returns_expected_petri_area() -> None:
    result = calibrate_from_image_size(1000, 1000)

    assert math.isclose(result.petri_area_mm2, math.pi * (55.0 / 2.0) ** 2)


def test_calibration_from_circle_diameter_uses_pixel_value() -> None:
    result = calibrate_from_petri_diameter_px(550.0)

    assert math.isclose(result.mm_per_pixel, 0.1)
