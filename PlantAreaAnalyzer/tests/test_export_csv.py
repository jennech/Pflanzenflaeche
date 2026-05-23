from __future__ import annotations

import csv
import json
from pathlib import Path

from analysis.measurement import MeasurementResult
from analysis.petri_detection import PetriCircle
from analysis.settings import AnalysisSettings, HSVThresholds
from exports.export_csv import export_analysis_to_csv


def test_export_analysis_to_csv_writes_header_and_appends(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    image_path = tmp_path / "bild_a.png"
    measurement = MeasurementResult(
        green_pixels=1234,
        green_area_mm2=56.78901,
        petri_area_mm2=2375.83,
        coverage_percent=2.39012,
    )
    petri_circle = PetriCircle(center_x=100, center_y=120, radius=80)
    settings = AnalysisSettings(
        thresholds=HSVThresholds(h_min=10, h_max=90, s_min=20, s_max=240),
        min_object_area_px=42,
        max_object_area_px=9000,
        green_dominance_margin=7,
        green_index_min=3,
        leaf_fill_px=2,
        pale_leaf_expansion_px=5,
        inner_dish_factor=0.75,
        morphology_kernel_size=3,
        manual_petri_circle=(100, 120, 80),
        excluded_component_points=((5, 6), (7, 8)),
    )

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
    assert json.loads(rows[0]["manual_petri_circle"]) == [100, 120, 80]
    assert json.loads(rows[0]["excluded_component_points"]) == [[5, 6], [7, 8]]
