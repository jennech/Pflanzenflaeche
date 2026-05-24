from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

import numpy as np


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
class AnalysisSettings:
    thresholds: HSVThresholds = field(default_factory=HSVThresholds)
    min_object_area_px: int = 120
    max_object_area_px: int = 50000
    green_dominance_margin: int = 12
    green_index_min: int = 8
    leaf_fill_px: int = 2
    pale_leaf_expansion_px: int = 12
    root_trim_px: int = 4
    inner_dish_factor: float = 0.90
    morphology_kernel_size: int = 3
    manual_petri_circle: tuple[int, int, int] | None = None
    excluded_component_points: tuple[tuple[int, int], ...] = ()
