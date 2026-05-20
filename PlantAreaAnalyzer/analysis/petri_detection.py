from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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
    contour_circle = detect_petri_circle_from_dark_region(gray)

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
        hough_circle = PetriCircle(
            center_x=int(round(selected[0])),
            center_y=int(round(selected[1])),
            radius=int(round(selected[2])),
        )
        if contour_circle is not None:
            center_distance = np.hypot(
                hough_circle.center_x - contour_circle.center_x,
                hough_circle.center_y - contour_circle.center_y,
            )
            if center_distance > contour_circle.radius * 0.25:
                return contour_circle
        return hough_circle

    if contour_circle is not None:
        return contour_circle

    return PetriCircle(
        center_x=width // 2,
        center_y=height // 2,
        radius=max(1, int(min_dim * 0.45)),
    )


def detect_petri_circle_from_dark_region(gray_image: np.ndarray) -> Optional[PetriCircle]:
    """Fallback detector for wide images where Hough misses the dish rim."""

    height, width = gray_image.shape
    min_dim = min(height, width)
    blurred = cv2.GaussianBlur(gray_image, (7, 7), 0)
    _, dark_mask = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU,
    )

    kernel_size = max(5, min_dim // 80)
    kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(
        dark_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    candidates: list[tuple[float, PetriCircle]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_dim * min_dim * 0.04:
            continue

        (center_x, center_y), radius = cv2.minEnclosingCircle(contour)
        if radius < min_dim * 0.18 or radius > min_dim * 0.60:
            continue

        circle_area = np.pi * radius * radius
        fill_ratio = area / circle_area if circle_area else 0
        if fill_ratio < 0.35:
            continue

        # Prefer large, compact dark regions over rectangular labels or grid artifacts.
        score = area * fill_ratio
        candidates.append(
            (
                score,
                PetriCircle(
                    center_x=int(round(center_x)),
                    center_y=int(round(center_y)),
                    radius=int(round(radius)),
                ),
            )
        )

    if not candidates:
        return None

    return max(candidates, key=lambda candidate: candidate[0])[1]


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
