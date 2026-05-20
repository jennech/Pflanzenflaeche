import numpy as np

from analysis.green_segmentation import build_green_dominance_mask
from analysis.green_segmentation import filter_small_components


def test_green_dominance_filters_blue_color_fringe() -> None:
    bgr_image = np.array(
        [
            [[20, 90, 20], [90, 95, 20]],
        ],
        dtype=np.uint8,
    )

    mask = build_green_dominance_mask(bgr_image, min_margin=20)

    assert mask[0, 0] == 255
    assert mask[0, 1] == 0


def test_filter_small_components_keeps_only_large_regions() -> None:
    mask = np.zeros((6, 6), dtype=np.uint8)
    mask[0, 0] = 255
    mask[2:5, 2:5] = 255

    filtered = filter_small_components(mask, min_area_px=4)

    assert filtered[0, 0] == 0
    assert filtered[3, 3] == 255
