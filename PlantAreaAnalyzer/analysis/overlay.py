from __future__ import annotations

import cv2
import numpy as np


def build_green_overlay(
    rgb_image: np.ndarray,
    mask: np.ndarray,
    overlay_color: tuple[int, int, int] = (0, 255, 0),
    alpha: float = 0.35,
) -> np.ndarray:
    overlay = rgb_image.copy()
    overlay[mask > 0] = overlay_color
    return cv2.addWeighted(overlay, alpha, rgb_image, 1.0 - alpha, 0.0)
