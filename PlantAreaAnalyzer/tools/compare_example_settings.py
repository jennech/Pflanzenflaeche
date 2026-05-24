from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.auto_settings import suggest_analysis_settings
from analysis.green_segmentation import analyze_green_area
from analysis.settings import AnalysisSettings
from analysis.settings import HSVThresholds


EXAMPLES_DIR = PROJECT_ROOT / "data" / "examples"
EXAMPLES_CSV = EXAMPLES_DIR / "examples.csv"


@dataclass(frozen=True)
class ExampleReference:
    image_path: Path
    filename: str
    green_pixels: int
    settings: AnalysisSettings


def main() -> None:
    references = load_references(EXAMPLES_CSV)
    if not references:
        print(f"Keine Referenzwerte gefunden: {EXAMPLES_CSV}")
        return

    print("Bild; Referenz px; Auto px; Abweichung %; Auto-Werte")
    for reference in references:
        suggested = suggest_analysis_settings(reference.image_path)
        result = analyze_green_area(reference.image_path, settings=suggested)
        deviation = percent_deviation(result.measurement.green_pixels, reference.green_pixels)
        print(
            f"{reference.filename}; "
            f"{reference.green_pixels}; "
            f"{result.measurement.green_pixels}; "
            f"{deviation:+.1f}%; "
            f"{format_settings(suggested)}"
        )


def load_references(csv_path: Path) -> list[ExampleReference]:
    if not csv_path.exists():
        return []

    references: list[ExampleReference] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        for row in csv.DictReader(csv_file):
            image_path = Path(row["image_path"])
            if not image_path.exists():
                fallback_path = EXAMPLES_DIR / row["original_filename"]
                image_path = fallback_path
            if not image_path.exists():
                continue

            references.append(
                ExampleReference(
                    image_path=image_path,
                    filename=row["original_filename"],
                    green_pixels=int(row["green_pixels"]),
                    settings=settings_from_row(row),
                )
            )
    return references


def settings_from_row(row: dict[str, str]) -> AnalysisSettings:
    return AnalysisSettings(
        thresholds=HSVThresholds(
            h_min=int(float(row["h_min"])),
            h_max=int(float(row["h_max"])),
            s_min=int(float(row["s_min"])),
            s_max=int(float(row["s_max"])),
            v_min=int(float(row["v_min"])),
            v_max=int(float(row["v_max"])),
        ),
        min_object_area_px=int(float(row["min_object_area_px"])),
        max_object_area_px=int(float(row["max_object_area_px"])),
        green_dominance_margin=int(float(row["green_dominance_margin"])),
        green_index_min=int(float(row["green_index_min"])),
        leaf_fill_px=int(float(row["leaf_fill_px"])),
        pale_leaf_expansion_px=int(float(row["pale_leaf_expansion_px"])),
        root_trim_px=int(float(row["root_trim_px"])),
        inner_dish_factor=float(row["inner_dish_percent"]) / 100.0,
        morphology_kernel_size=int(float(row["morphology_kernel_size"])),
    )


def percent_deviation(value: int, reference: int) -> float:
    if reference == 0:
        return 0.0 if value == 0 else 100.0
    return ((value - reference) / reference) * 100.0


def format_settings(settings: AnalysisSettings) -> str:
    t = settings.thresholds
    return (
        f"H {t.h_min}-{t.h_max}, S {t.s_min}-{t.s_max}, V {t.v_min}-{t.v_max}, "
        f"Min {settings.min_object_area_px}, Max {settings.max_object_area_px}, "
        f"GA {settings.green_dominance_margin}, GI {settings.green_index_min}, "
        f"Fuell {settings.leaf_fill_px}, Blass {settings.pale_leaf_expansion_px}, "
        f"Wurzel {settings.root_trim_px}, Innen {settings.inner_dish_factor:.2f}"
    )


if __name__ == "__main__":
    main()
