from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.auto_settings import suggest_analysis_settings
from analysis.green_segmentation import analyze_green_area
from analysis.settings import AnalysisSettings
from analysis.settings import HSVThresholds


REFERENCE_SETTINGS_JSON = PROJECT_ROOT / "data" / "reference" / "reference_settings.json"


@dataclass(frozen=True)
class ExampleReference:
    image_path: Path
    filename: str
    green_pixels: int
    settings: AnalysisSettings


def main() -> None:
    references = load_references(REFERENCE_SETTINGS_JSON)
    if not references:
        print(f"Keine Referenzwerte gefunden: {REFERENCE_SETTINGS_JSON}")
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


def load_references(json_path: Path) -> list[ExampleReference]:
    if not json_path.exists():
        return []

    with json_path.open(encoding="utf-8") as reference_file:
        data = json.load(reference_file)

    references = []
    for entry in data.get("references", []):
        if not isinstance(entry, dict):
            continue

        image_path = resolve_reference_image_path(entry, json_path.parent)
        if image_path is None:
            continue

        references.append(
            ExampleReference(
                image_path=image_path,
                filename=image_path.name,
                green_pixels=int(entry.get("expected_green_pixels", 0)),
                settings=settings_from_entry(entry),
            )
        )

    return references


def resolve_reference_image_path(entry: dict[str, object], base_dir: Path) -> Path | None:
    image_value = entry.get("image", "")
    if not isinstance(image_value, str):
        return None

    image_path = Path(image_value)
    for candidate in (image_path, base_dir / image_path, PROJECT_ROOT / image_path):
        if candidate.exists():
            return candidate
    return None


def settings_from_entry(entry: dict[str, object]) -> AnalysisSettings:
    settings = entry["settings"]
    if not isinstance(settings, dict):
        raise TypeError("settings must be an object")

    return AnalysisSettings(
        thresholds=HSVThresholds(
            h_min=int(float(settings["h_min"])),
            h_max=int(float(settings["h_max"])),
            s_min=int(float(settings["s_min"])),
            s_max=int(float(settings["s_max"])),
            v_min=int(float(settings["v_min"])),
            v_max=int(float(settings["v_max"])),
        ),
        min_object_area_px=int(float(settings["min_object_area_px"])),
        max_object_area_px=int(float(settings["max_object_area_px"])),
        green_dominance_margin=int(float(settings["green_dominance_margin"])),
        green_index_min=int(float(settings["green_index_min"])),
        leaf_fill_px=int(float(settings["leaf_fill_px"])),
        pale_leaf_expansion_px=int(float(settings["pale_leaf_expansion_px"])),
        root_trim_px=int(float(settings["root_trim_px"])),
        inner_dish_factor=float(settings["inner_dish_percent"]) / 100.0,
        morphology_kernel_size=int(float(settings["morphology_kernel_size"])),
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
