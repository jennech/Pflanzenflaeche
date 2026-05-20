import numpy as np

from analysis.petri_detection import PetriCircle
from analysis.petri_detection import build_petri_mask


def test_build_petri_mask_creates_circular_roi() -> None:
    mask = build_petri_mask((100, 100), PetriCircle(50, 50, 20), shrink_factor=1.0)

    assert mask[50, 50] == 255
    assert mask[0, 0] == 0
