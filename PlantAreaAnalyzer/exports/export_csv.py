from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from analysis.measurement import MeasurementResult
from analysis.petri_detection import PetriCircle
from analysis.settings import AnalysisSettings

ANALYSIS_VERSION = "mvp-1"

CSV_FIELDNAMES = [
    "timestamp",
    "analysis_version",
    "image_path",
    "original_filename",
    "green_pixels",
    "plant_area_mm2",
    "petri_area_mm2",
    "coverage_percent",
    "petri_center_x",
    "petri_center_y",
    "petri_radius_px",
    "inner_dish_percent",
    "h_min",
    "h_max",
    "s_min",
    "s_max",
    "v_min",
    "v_max",
    "min_object_area_px",
    "max_object_area_px",
    "green_dominance_margin",
    "green_index_min",
    "leaf_fill_px",
    "pale_leaf_expansion_px",
    "root_trim_px",
    "morphology_kernel_size",
    "manual_petri_circle",
    "excluded_component_points",
    "manual_leaf_points",
    "manual_leaf_radius_px",
]


def export_analysis_to_csv(
    csv_path: Path,
    image_path: Path,
    measurement: MeasurementResult,
    petri_circle: PetriCircle,
    settings: AnalysisSettings,
) -> None:
    """Append one analysis result to a CSV file, creating a header if needed."""

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0

    with csv_path.open("a", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(
            build_export_row(
                image_path=image_path,
                measurement=measurement,
                petri_circle=petri_circle,
                settings=settings,
            )
        )


def build_export_row(
    image_path: Path,
    measurement: MeasurementResult,
    petri_circle: PetriCircle,
    settings: AnalysisSettings,
) -> dict[str, str | int | float]:
    thresholds = settings.thresholds
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "analysis_version": ANALYSIS_VERSION,
        "image_path": str(image_path),
        "original_filename": image_path.name,
        "green_pixels": measurement.green_pixels,
        "plant_area_mm2": round(measurement.green_area_mm2, 4),
        "petri_area_mm2": round(measurement.petri_area_mm2, 4),
        "coverage_percent": round(measurement.coverage_percent, 4),
        "petri_center_x": petri_circle.center_x,
        "petri_center_y": petri_circle.center_y,
        "petri_radius_px": petri_circle.radius,
        "inner_dish_percent": round(settings.inner_dish_factor * 100.0, 2),
        "h_min": thresholds.h_min,
        "h_max": thresholds.h_max,
        "s_min": thresholds.s_min,
        "s_max": thresholds.s_max,
        "v_min": thresholds.v_min,
        "v_max": thresholds.v_max,
        "min_object_area_px": settings.min_object_area_px,
        "max_object_area_px": settings.max_object_area_px,
        "green_dominance_margin": settings.green_dominance_margin,
        "green_index_min": settings.green_index_min,
        "leaf_fill_px": settings.leaf_fill_px,
        "pale_leaf_expansion_px": settings.pale_leaf_expansion_px,
        "root_trim_px": settings.root_trim_px,
        "morphology_kernel_size": settings.morphology_kernel_size,
        "manual_petri_circle": json.dumps(settings.manual_petri_circle),
        "excluded_component_points": json.dumps(settings.excluded_component_points),
        "manual_leaf_points": json.dumps(settings.manual_leaf_points),
        "manual_leaf_radius_px": settings.manual_leaf_radius_px,
    }
