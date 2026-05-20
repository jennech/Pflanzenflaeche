from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class PetriCircle:
    center_x: int
    center_y: int
    radius: int


def detect_petri_circle(bgr_image: np.ndarray) -> PetriCircle:
    """Detect the petri dish so analysis can ignore the background and rim."""

    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 7)
    height, width = gray.shape
    min_dim = min(height, width)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=max(1, min_dim // 2),
        param1=120,
        param2=35,
        minRadius=int(min_dim * 0.25),
        maxRadius=int(min_dim * 0.6),
    )

    if circles is not None and len(circles[0]) > 0:
        selected = max(circles[0], key=lambda entry: entry[2])
        return PetriCircle(
            center_x=int(round(selected[0])),
            center_y=int(round(selected[1])),
            radius=int(round(selected[2])),
        )

    return PetriCircle(
        center_x=width // 2,
        center_y=height // 2,
        radius=max(1, int(min_dim * 0.45)),
    )


def build_petri_mask(
    image_shape: tuple[int, int],
    circle: PetriCircle,
    shrink_factor: float = 0.90,
) -> np.ndarray:
    """Build a circular mask that keeps the inner dish area only."""

    height, width = image_shape
    mask = np.zeros((height, width), dtype=np.uint8)
    inner_radius = max(1, int(round(circle.radius * shrink_factor)))
    cv2.circle(mask, (circle.center_x, circle.center_y), inner_radius, 255, -1)
    return mask


def placeholder_detection_note() -> str:
    return (
        "Petrischalen-Erkennung ist im MVP noch nicht voll manuell. "
        "Aktuell wird eine Hough-Kreis-Erkennung mit Fallback verwendet."
    )
