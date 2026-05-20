import numpy as np
import cv2

from analysis.petri_detection import PetriCircle
from analysis.petri_detection import build_petri_mask
from analysis.petri_detection import detect_petri_circle_from_dark_region
from analysis.petri_detection import select_best_hough_circle


def test_build_petri_mask_creates_circular_roi() -> None:
    mask = build_petri_mask((100, 100), PetriCircle(50, 50, 20), shrink_factor=1.0)

    assert mask[50, 50] == 255
    assert mask[0, 0] == 0


def test_dark_region_detection_ignores_grid_on_wide_image() -> None:
    gray_image = np.full((220, 420), 235, dtype=np.uint8)
    cv2.circle(gray_image, (105, 110), 70, 70, -1)
    cv2.rectangle(gray_image, (260, 70), (360, 170), 190, 2)

    circle = detect_petri_circle_from_dark_region(gray_image)

    assert circle is not None
    assert abs(circle.center_x - 105) <= 8
    assert abs(circle.center_y - 110) <= 8
    assert abs(circle.radius - 70) <= 8


def test_hough_selection_prefers_contour_sized_circle_over_largest_shadow() -> None:
    hough_circles = np.array(
        [
            [101.0, 99.0, 72.0],
            [102.0, 100.0, 92.0],
        ],
        dtype=np.float32,
    )

    circle = select_best_hough_circle(
        hough_circles,
        contour_circle=PetriCircle(100, 100, 70),
        min_dim=220,
    )

    assert circle.radius == 72
