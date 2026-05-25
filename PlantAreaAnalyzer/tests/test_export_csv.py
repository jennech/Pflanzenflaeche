from __future__ import annotations

import csv
import json
from pathlib import Path

from analysis.measurement import MeasurementResult
from analysis.petri_detection import PetriCircle
from analysis.settings import AnalysisSettings, HSVThresholds
from exports.export_csv import export_analysis_to_csv


def measurement_result() -> MeasurementResult:
    return MeasurementResult(
        green_pixels=1234,
        green_area_mm2=56.78901,
        petri_area_mm2=2375.83,
        coverage_percent=2.39012,
    )


def analysis_settings() -> AnalysisSettings:
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=10, h_max=90, s_min=20, s_max=240),
        min_object_area_px=42,
        max_object_area_px=9000,
        green_dominance_margin=7,
        green_index_min=3,
        leaf_fill_px=2,
        pale_leaf_expansion_px=5,
        root_trim_px=6,
        inner_dish_factor=0.75,
        morphology_kernel_size=3,
        manual_petri_circle=(100, 120, 80),
        excluded_component_points=((5, 6), (7, 8)),
        manual_leaf_points=((9, 10),),
        manual_leaf_radius_px=14,
        manual_leaf_patches=((9, 10, 14), (20, 21, 6)),
    )


def test_export_analysis_to_csv_writes_header_and_appends(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    image_path = tmp_path / "bild_a.png"
    measurement = measurement_result()
    petri_circle = PetriCircle(center_x=100, center_y=120, radius=80)
    settings = analysis_settings()

    export_analysis_to_csv(
        csv_path=csv_path,
        image_path=image_path,
        measurement=measurement,
        petri_circle=petri_circle,
        settings=settings,
    )
    export_analysis_to_csv(
        csv_path=csv_path,
        image_path=image_path,
        measurement=measurement,
        petri_circle=petri_circle,
        settings=settings,
    )

    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 2
    assert rows[0]["original_filename"] == "bild_a.png"
    assert rows[0]["green_pixels"] == "1234"
    assert rows[0]["plant_area_mm2"] == "56.789"
    assert rows[0]["coverage_percent"] == "2.3901"
    assert rows[0]["petri_center_x"] == "100"
    assert rows[0]["inner_dish_percent"] == "75.0"
    assert rows[0]["h_min"] == "10"
    assert rows[0]["root_trim_px"] == "6"
    assert json.loads(rows[0]["manual_petri_circle"]) == [100, 120, 80]
    assert json.loads(rows[0]["excluded_component_points"]) == [[5, 6], [7, 8]]
    assert json.loads(rows[0]["manual_leaf_points"]) == [[9, 10]]
    assert rows[0]["manual_leaf_radius_px"] == "14"
    assert json.loads(rows[0]["manual_leaf_patches"]) == [[9, 10, 14], [20, 21, 6]]


def test_export_analysis_to_csv_upgrades_existing_legacy_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    image_path = tmp_path / "bild_b.png"
    petri_circle = PetriCircle(center_x=100, center_y=120, radius=80)
    settings = analysis_settings()

    legacy_fieldnames = [
        "timestamp",
        "analysis_version",
        "image_path",
        "original_filename",
        "green_pixels",
    ]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=legacy_fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "timestamp": "2026-01-01T10:00:00",
                "analysis_version": "mvp-1",
                "image_path": "/tmp/alt.png",
                "original_filename": "alt.png",
                "green_pixels": "99",
            }
        )

    export_analysis_to_csv(
        csv_path=csv_path,
        image_path=image_path,
        measurement=measurement_result(),
        petri_circle=petri_circle,
        settings=settings,
    )

    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 2
    assert rows[0]["original_filename"] == "alt.png"
    assert rows[0]["manual_leaf_patches"] == ""
    assert rows[1]["original_filename"] == "bild_b.png"
    assert json.loads(rows[1]["manual_leaf_patches"]) == [[9, 10, 14], [20, 21, 6]]
