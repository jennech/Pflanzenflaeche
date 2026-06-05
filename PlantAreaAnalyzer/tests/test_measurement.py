import math

import numpy as np

from analysis.calibration import CalibrationResult
from analysis.measurement import measure_green_area


def test_measurement_counts_green_pixels() -> None:
    mask = np.array(
        [
            [0, 255, 0],
            [255, 255, 0],
        ],
        dtype=np.uint8,
    )
    calibration = CalibrationResult(
        petri_diameter_mm=55.0,
        pixel_diameter=100.0,
        mm_per_pixel=0.5,
        petri_area_mm2=2000.0,
    )

    result = measure_green_area(mask, calibration)

    assert result.green_pixels == 3
    assert math.isclose(result.green_area_mm2, 0.75)
    assert math.isclose(result.coverage_percent, 0.0375)
