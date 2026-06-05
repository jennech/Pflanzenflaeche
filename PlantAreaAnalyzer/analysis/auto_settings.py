from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from analysis.green_segmentation import build_green_dominance_mask
from analysis.green_segmentation import build_green_index_mask
from analysis.green_segmentation import build_pale_leaf_expansion_mask
from analysis.green_segmentation import fill_leaf_gaps
from analysis.green_segmentation import filter_components_by_area
from analysis.green_segmentation import suppress_thin_protrusions
from analysis.petri_detection import PetriCircle
from analysis.petri_detection import build_petri_mask
from analysis.petri_detection import detect_petri_circle
from analysis.settings import AnalysisSettings
from analysis.settings import HSVThresholds

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SETTINGS_JSON = PROJECT_ROOT / "data" / "reference" / "reference_settings.json"
REFERENCE_SETTINGS_DIR = REFERENCE_SETTINGS_JSON.parent
REFERENCE_DISTANCE_LIMIT = 0.42
MAX_REFERENCE_MASK_DISH_RATIO = 0.45
MAX_REFERENCE_COMPONENT_DISH_RATIO = 0.32
MAX_REFERENCE_EDGE_AREA_RATIO = 0.18


def suggest_analysis_settings(
    image_path: Path,
    base_settings: AnalysisSettings | None = None,
    manual_petri_circle: tuple[int, int, int] | None = None,
) -> AnalysisSettings:
    """Derive conservative segmentation defaults from the current image."""

    base_settings = base_settings or AnalysisSettings()
    bgr_image = cv2.imread(str(image_path))
    if bgr_image is None:
        raise ValueError(f"Bild konnte nicht geladen werden: {image_path}")

    reference_settings = load_reference_settings_for_similar_image(image_path, bgr_image)
    if reference_settings is not None:
        return reference_settings

    petri_circle = (
        PetriCircle(*manual_petri_circle)
        if manual_petri_circle is not None
        else detect_petri_circle(bgr_image)
    )
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    dish_mask = build_petri_mask(
        hsv_image.shape[:2],
        petri_circle,
        shrink_factor=min(base_settings.inner_dish_factor, 0.88),
    )
    candidate_mask = build_leaf_candidate_mask(bgr_image, hsv_image, dish_mask)

    if not np.any(candidate_mask):
        return conservative_dark_leaf_settings(base_settings)

    hue = hsv_image[:, :, 0][candidate_mask]
    saturation = hsv_image[:, :, 1][candidate_mask]
    value = hsv_image[:, :, 2][candidate_mask]
    blue, green, red = cv2.split(bgr_image.astype(np.int16))
    excess_green = ((2 * green) - red - blue)[candidate_mask]
    green_margin = np.minimum(green - red, green - blue)[candidate_mask]

    thresholds = HSVThresholds(
        h_min=clamp_int(percentile(hue, 5) - 12, 0, 179),
        h_max=clamp_int(percentile(hue, 95) + 12, 0, 179),
        s_min=clamp_int(percentile(saturation, 8) - 20, 18, 210),
        s_max=255,
        v_min=clamp_int(percentile(value, 5) - 20, 20, 180),
        v_max=255,
    )

    min_area = max(80, int(candidate_mask.sum() * 0.003))
    max_area = max(6000, int(candidate_mask.sum() * 0.65))
    data_driven_settings = AnalysisSettings(
        thresholds=thresholds,
        min_object_area_px=min(min_area, 2500),
        max_object_area_px=min(max_area, 120000),
        green_dominance_margin=clamp_int(percentile(green_margin, 20) - 6, 4, 45),
        green_index_min=clamp_int(percentile(excess_green, 25) - 8, -20, 80),
        leaf_fill_px=3,
        pale_leaf_expansion_px=8,
        root_trim_px=base_settings.root_trim_px,
        inner_dish_factor=base_settings.inner_dish_factor,
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )
    candidate_settings = [
        base_settings,
        stricter_root_variant(base_settings, manual_petri_circle),
        data_driven_settings,
        dark_leaf_high_saturation_settings(base_settings, manual_petri_circle),
        balanced_root_safe_settings(base_settings, manual_petri_circle),
        medium_aware_leaf_settings(base_settings, manual_petri_circle),
        root_strict_settings(base_settings, manual_petri_circle),
        broad_strict_leaf_settings(base_settings, manual_petri_circle),
        contrast_strict_leaf_settings(base_settings, manual_petri_circle),
        pale_leaf_settings(base_settings, manual_petri_circle),
        pale_leaf_base_root_settings(base_settings, manual_petri_circle),
    ]
    if should_try_small_pale_core_settings(
        bgr_image,
        hsv_image,
        petri_circle,
        candidate_mask,
    ):
        candidate_settings.append(small_pale_core_settings(base_settings, manual_petri_circle))

    return choose_best_settings(
        bgr_image=bgr_image,
        hsv_image=hsv_image,
        petri_circle=petri_circle,
        base_settings=base_settings,
        candidate_settings=candidate_settings,
    )


def choose_best_settings(
    bgr_image: np.ndarray,
    hsv_image: np.ndarray,
    petri_circle: PetriCircle,
    base_settings: AnalysisSettings,
    candidate_settings: list[AnalysisSettings],
) -> AnalysisSettings:
    leaf_core_mask = build_high_confidence_leaf_core_mask(
        bgr_image,
        hsv_image,
        petri_circle,
    )
    scored_settings: list[tuple[float, int, AnalysisSettings]] = []
    for settings in candidate_settings:
        mask = build_mask_for_scoring(bgr_image, hsv_image, petri_circle, settings)
        scored_settings.append(
            (
                score_mask(mask, petri_circle, leaf_core_mask),
                int(np.count_nonzero(mask)),
                settings,
            )
        )

    if not scored_settings:
        return conservative_dark_leaf_settings(base_settings)

    best_score, best_area, best_settings = max(scored_settings, key=lambda entry: entry[0])

    strict_candidates = [
        (score, area, settings)
        for score, area, settings in scored_settings
        if settings.green_dominance_margin >= 70 and area >= 5_000
    ]
    if best_settings.green_dominance_margin < 30 and strict_candidates:
        strict_score, strict_area, strict_settings = max(
            strict_candidates,
            key=lambda entry: entry[0],
        )
        # A broad pale/dark mask can look plausible by area alone, but may include
        # halos around leaves. Prefer the stricter green candidate when it captures
        # a substantial leaf signal and the broad mask is much larger.
        if best_area > strict_area * 1.7 and strict_score > best_score * 0.45:
            return strict_settings

    return best_settings


def load_reference_settings_for_similar_image(
    image_path: Path,
    bgr_image: np.ndarray,
) -> AnalysisSettings | None:
    """Use the closest visually similar curated reference as a start."""

    references = load_reference_settings()
    if not references:
        return None

    current_signature = image_similarity_signature(bgr_image)
    closest_reference: dict[str, object] | None = None
    closest_distance = float("inf")
    for reference in references:
        reference_path = reference_image_path(reference)
        if reference_path is None:
            continue

        reference_image = cv2.imread(str(reference_path))
        if reference_image is None:
            continue

        distance = signature_distance(
            current_signature,
            image_similarity_signature(reference_image),
        )
        if distance <= closest_distance:
            closest_distance = distance
            closest_reference = reference

    if closest_reference is None or closest_distance > REFERENCE_DISTANCE_LIMIT:
        return None

    try:
        reference_settings = settings_from_reference_entry(closest_reference)
    except (KeyError, TypeError, ValueError):
        return None

    if not reference_settings_is_plausible_for_image(bgr_image, reference_settings):
        return None

    return reference_settings


def reference_settings_is_plausible_for_image(
    bgr_image: np.ndarray,
    settings: AnalysisSettings,
) -> bool:
    """Reject curated starts that clearly classify medium as leaf area."""

    try:
        petri_circle = detect_petri_circle(bgr_image)
    except ValueError:
        return True

    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    mask = build_mask_for_scoring(bgr_image, hsv_image, petri_circle, settings)
    dish_mask = build_petri_mask(
        mask.shape,
        petri_circle,
        shrink_factor=settings.inner_dish_factor,
    )
    dish_area = max(1, int(np.count_nonzero(dish_mask)))
    mask_area = int(np.count_nonzero(mask))
    if mask_area == 0:
        return True

    if mask_area / dish_area > MAX_REFERENCE_MASK_DISH_RATIO:
        return False

    num_labels, labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, 8)
    if num_labels <= 1:
        return True

    edge_area = 0
    largest_component = max(
        int(stats[label, cv2.CC_STAT_AREA])
        for label in range(1, num_labels)
    )
    for label in range(1, num_labels):
        component = labels == label
        if touches_analysis_edge(component, petri_circle):
            edge_area += int(stats[label, cv2.CC_STAT_AREA])

    if mask_area / dish_area > 0.05 and edge_area / mask_area > MAX_REFERENCE_EDGE_AREA_RATIO:
        return False

    return largest_component / dish_area <= MAX_REFERENCE_COMPONENT_DISH_RATIO


def load_reference_settings() -> list[dict[str, object]]:
    if not REFERENCE_SETTINGS_JSON.exists():
        return []

    with REFERENCE_SETTINGS_JSON.open(encoding="utf-8") as reference_file:
        data = json.load(reference_file)

    references = data.get("references", [])
    return references if isinstance(references, list) else []


def reference_image_path(reference: dict[str, object]) -> Path | None:
    image_value = reference.get("image", "")
    if not isinstance(image_value, str):
        return None

    image_path = Path(image_value)
    candidates = (
        image_path,
        REFERENCE_SETTINGS_DIR / image_path,
        PROJECT_ROOT / image_path,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def image_similarity_signature(bgr_image: np.ndarray) -> np.ndarray:
    hsv_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
    try:
        petri_circle = detect_petri_circle(bgr_image)
        dish_mask = build_petri_mask(hsv_image.shape[:2], petri_circle, shrink_factor=0.88)
    except ValueError:
        dish_mask = np.full(hsv_image.shape[:2], 255, dtype=np.uint8)

    dish_pixels = dish_mask > 0
    candidate_mask = build_leaf_candidate_mask(bgr_image, hsv_image, dish_mask)
    candidate_pixels = candidate_mask > 0
    dish_area = max(1, int(np.count_nonzero(dish_pixels)))
    candidate_ratio = np.count_nonzero(candidate_pixels) / dish_area

    dish_hsv = hsv_image[dish_pixels]
    if dish_hsv.size == 0:
        dish_hsv = hsv_image.reshape(-1, 3)

    if np.any(candidate_pixels):
        leaf_hsv = hsv_image[candidate_pixels]
    else:
        leaf_hsv = dish_hsv

    return np.array(
        [
            float(np.mean(dish_hsv[:, 0]) / 179.0),
            float(np.std(dish_hsv[:, 0]) / 179.0),
            float(np.mean(dish_hsv[:, 1]) / 255.0),
            float(np.std(dish_hsv[:, 1]) / 255.0),
            float(np.mean(dish_hsv[:, 2]) / 255.0),
            float(np.std(dish_hsv[:, 2]) / 255.0),
            float(min(candidate_ratio * 8.0, 1.0)),
            float(np.median(leaf_hsv[:, 0]) / 179.0),
            float(np.median(leaf_hsv[:, 1]) / 255.0),
            float(np.median(leaf_hsv[:, 2]) / 255.0),
        ],
        dtype=np.float32,
    )


def signature_distance(first: np.ndarray, second: np.ndarray) -> float:
    weights = np.array([0.6, 0.3, 1.0, 0.7, 0.8, 0.5, 1.4, 0.8, 1.2, 0.8])
    return float(np.linalg.norm((first - second) * weights))


def settings_from_reference_entry(reference: dict[str, object]) -> AnalysisSettings:
    settings = reference["settings"]
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


def build_mask_for_scoring(
    bgr_image: np.ndarray,
    hsv_image: np.ndarray,
    petri_circle: PetriCircle,
    settings: AnalysisSettings,
) -> np.ndarray:
    hsv_mask = cv2.inRange(
        hsv_image,
        settings.thresholds.lower_bound(),
        settings.thresholds.upper_bound(),
    )
    dominance_mask = build_green_dominance_mask(
        bgr_image,
        settings.green_dominance_margin,
    )
    strict_mask = cv2.bitwise_and(hsv_mask, dominance_mask)
    index_mask = build_green_index_mask(bgr_image, hsv_image, settings)
    mask = cv2.bitwise_or(strict_mask, index_mask)
    dish_mask = build_petri_mask(
        mask.shape,
        petri_circle,
        shrink_factor=settings.inner_dish_factor,
    )
    mask = cv2.bitwise_and(mask, dish_mask)
    pale_leaf_mask = build_pale_leaf_expansion_mask(
        bgr_image,
        hsv_image,
        mask,
        settings.pale_leaf_expansion_px,
        settings,
    )
    mask = cv2.bitwise_or(mask, cv2.bitwise_and(pale_leaf_mask, dish_mask))
    mask = fill_leaf_gaps(mask, settings.leaf_fill_px)

    kernel_size = max(1, settings.morphology_kernel_size)
    kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
    cleaned_mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)
    cleaned_mask = filter_components_by_area(
        cleaned_mask,
        min_area_px=settings.min_object_area_px,
        max_area_px=settings.max_object_area_px,
    )
    return suppress_thin_protrusions(cleaned_mask, settings.root_trim_px)


def score_mask(
    mask: np.ndarray,
    petri_circle: PetriCircle,
    leaf_core_mask: np.ndarray | None = None,
) -> float:
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if num_labels <= 1:
        return -1_000_000.0

    component_scores: list[float] = []
    total_area = 0
    thin_penalty = 0.0
    edge_penalty = 0.0
    weak_component_penalty = 0.0
    satellite_penalty = 0.0
    core_overlap_area = 0
    component_areas: list[int] = []
    for label in range(1, num_labels):
        area = int(stats[label, cv2.CC_STAT_AREA])
        width = int(stats[label, cv2.CC_STAT_WIDTH])
        height = int(stats[label, cv2.CC_STAT_HEIGHT])
        if area <= 0:
            continue

        component = labels == label
        total_area += area
        component_areas.append(area)
        short_side = max(1, min(width, height))
        long_side = max(width, height)
        aspect_ratio = long_side / short_side
        fill_ratio = area / max(1, width * height)
        component_score = min(area, 20_000) * min(1.0, fill_ratio + 0.25)
        if aspect_ratio > 3.5:
            thin_penalty += area * (aspect_ratio - 3.5)
        if touches_analysis_edge(component, petri_circle):
            edge_penalty += area * 1.5
        if leaf_core_mask is not None:
            component_core_area = int(np.count_nonzero(component & leaf_core_mask))
            core_overlap_area += component_core_area
            core_overlap_ratio = component_core_area / max(1, area)
            if component_core_area == 0:
                weak_component_penalty += area * 1.4
            elif core_overlap_ratio < 0.08:
                weak_component_penalty += area * (0.08 - core_overlap_ratio) * 6.0
        component_scores.append(component_score)

    if total_area == 0:
        return -1_000_000.0

    if component_areas:
        largest_area = max(component_areas)
        satellite_area = sum(area for area in component_areas if area < largest_area * 0.22)
        satellite_penalty += satellite_area * 0.65
        if len(component_areas) > 8:
            satellite_penalty += (len(component_areas) - 8) * 2200.0

    dish_area = np.pi * petri_circle.radius * petri_circle.radius
    coverage = total_area / max(1.0, dish_area)
    plausible_area_score = total_area
    if coverage < 0.015:
        plausible_area_score -= (0.015 - coverage) * dish_area * 8.0
    if coverage > 0.23:
        plausible_area_score -= (coverage - 0.23) * dish_area * 5.0

    core_precision_score = 0.0
    if leaf_core_mask is not None:
        core_area = int(np.count_nonzero(leaf_core_mask))
        if core_area > 0:
            core_recall = core_overlap_area / core_area
            outside_core_ratio = max(0.0, (total_area - core_overlap_area) / total_area)
            core_precision_score += core_recall * 12_000.0
            if outside_core_ratio > 0.86:
                core_precision_score -= (outside_core_ratio - 0.86) * total_area * 3.0

    large_components = sum(1 for score in component_scores if score > 300)
    plant_count_score = 5000.0 - abs(large_components - 4) * 1200.0
    return (
        plausible_area_score
        + plant_count_score
        + core_precision_score
        - thin_penalty
        - edge_penalty
        - weak_component_penalty
        - satellite_penalty
    )


def build_high_confidence_leaf_core_mask(
    bgr_image: np.ndarray,
    hsv_image: np.ndarray,
    petri_circle: PetriCircle,
) -> np.ndarray:
    """Find conservative leaf cores used only to judge auto-setting candidates."""

    dish_mask = build_petri_mask(hsv_image.shape[:2], petri_circle, shrink_factor=0.84)
    blue, green, red = cv2.split(bgr_image.astype(np.int16))
    hue = hsv_image[:, :, 0]
    saturation = hsv_image[:, :, 1]
    value = hsv_image[:, :, 2]
    excess_green = (2 * green) - red - blue
    green_margin = np.minimum(green - red, green - blue)

    core = (
        (dish_mask > 0)
        & (hue >= 25)
        & (hue <= 130)
        & (saturation >= 95)
        & (value >= 18)
        & (green_margin >= 4)
        & (excess_green >= 10)
    )
    core_mask = core.astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    core_mask = cv2.morphologyEx(core_mask, cv2.MORPH_OPEN, kernel)
    return keep_plausible_candidate_components(core_mask)


def should_try_small_pale_core_settings(
    bgr_image: np.ndarray,
    hsv_image: np.ndarray,
    petri_circle: PetriCircle,
    candidate_mask: np.ndarray,
) -> bool:
    """Only use the extreme tiny-plant mode when the whole image really looks tiny."""

    dish_area = max(1.0, np.pi * petri_circle.radius * petri_circle.radius)
    candidate_ratio = np.count_nonzero(candidate_mask) / dish_area
    core_mask = build_high_confidence_leaf_core_mask(bgr_image, hsv_image, petri_circle)
    core_ratio = np.count_nonzero(core_mask) / dish_area
    return core_ratio < 0.025 and candidate_ratio < 0.22


def touches_analysis_edge(component: np.ndarray, petri_circle: PetriCircle) -> bool:
    y_coords, x_coords = np.nonzero(component)
    if y_coords.size == 0:
        return False

    distances = np.hypot(x_coords - petri_circle.center_x, y_coords - petri_circle.center_y)
    return bool(np.any(distances > petri_circle.radius * 0.84))


def build_leaf_candidate_mask(
    bgr_image: np.ndarray,
    hsv_image: np.ndarray,
    dish_mask: np.ndarray,
) -> np.ndarray:
    blue, green, red = cv2.split(bgr_image.astype(np.int16))
    hue = hsv_image[:, :, 0]
    saturation = hsv_image[:, :, 1]
    value = hsv_image[:, :, 2]
    intensity = red + green + blue
    excess_green = (2 * green) - red - blue
    normalized_excess = excess_green / np.maximum(intensity, 1)

    dish_pixels = dish_mask > 0
    leaf_like = (
        dish_pixels
        & (hue >= 25)
        & (hue <= 115)
        & (saturation >= 18)
        & (value >= 25)
        & (value <= 245)
        & (green >= red - 8)
        & (green >= blue - 12)
        & ((excess_green >= 4) | (normalized_excess >= 0.035))
    )

    raw_mask = leaf_like.astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel)
    return keep_plausible_candidate_components(cleaned)


def keep_plausible_candidate_components(mask: np.ndarray) -> np.ndarray:
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    filtered = np.zeros_like(mask)

    for label in range(1, num_labels):
        area = stats[label, cv2.CC_STAT_AREA]
        width = stats[label, cv2.CC_STAT_WIDTH]
        height = stats[label, cv2.CC_STAT_HEIGHT]
        if area < 30:
            continue

        short_side = max(1, min(width, height))
        long_side = max(width, height)
        aspect_ratio = long_side / short_side
        fill_ratio = area / max(1, width * height)
        if aspect_ratio > 5.5 and fill_ratio < 0.45:
            continue

        filtered[labels == label] = 1

    return filtered.astype(bool)


def conservative_dark_leaf_settings(base_settings: AnalysisSettings) -> AnalysisSettings:
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=30, h_max=115, s_min=45, s_max=255, v_min=25),
        min_object_area_px=180,
        max_object_area_px=50000,
        green_dominance_margin=14,
        green_index_min=10,
        leaf_fill_px=3,
        pale_leaf_expansion_px=6,
        root_trim_px=base_settings.root_trim_px,
        inner_dish_factor=base_settings.inner_dish_factor,
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=base_settings.manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def stricter_root_variant(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    thresholds = base_settings.thresholds
    return AnalysisSettings(
        thresholds=HSVThresholds(
            h_min=thresholds.h_min,
            h_max=min(thresholds.h_max, 120),
            s_min=clamp_int(max(thresholds.s_min, 165), 0, 255),
            s_max=thresholds.s_max,
            v_min=thresholds.v_min,
            v_max=thresholds.v_max,
        ),
        min_object_area_px=max(base_settings.min_object_area_px, 300),
        max_object_area_px=min(base_settings.max_object_area_px, 50000),
        green_dominance_margin=max(base_settings.green_dominance_margin, 22),
        green_index_min=max(base_settings.green_index_min, 80),
        leaf_fill_px=min(base_settings.leaf_fill_px, 3),
        pale_leaf_expansion_px=min(base_settings.pale_leaf_expansion_px, 14),
        root_trim_px=max(base_settings.root_trim_px, 6),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.86),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def dark_leaf_high_saturation_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=30, h_max=120, s_min=128, s_max=255, v_min=20),
        min_object_area_px=300,
        max_object_area_px=75000,
        green_dominance_margin=17,
        green_index_min=80,
        leaf_fill_px=2,
        pale_leaf_expansion_px=30,
        root_trim_px=max(base_settings.root_trim_px, 10),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.86),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def balanced_root_safe_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    """Balanced candidate: tolerant enough for leaves, strict enough against medium/root flood."""
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=28, h_max=135, s_min=125, s_max=255, v_min=20),
        min_object_area_px=300,
        max_object_area_px=70000,
        green_dominance_margin=42,
        green_index_min=72,
        leaf_fill_px=0,
        pale_leaf_expansion_px=0,
        root_trim_px=max(base_settings.root_trim_px, 10),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.78),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def medium_aware_leaf_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    """Avoid muddy medium by demanding a clearer leaf-green hue and green surplus."""
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=50, h_max=135, s_min=130, s_max=255, v_min=0),
        min_object_area_px=300,
        max_object_area_px=120000,
        green_dominance_margin=42,
        green_index_min=78,
        leaf_fill_px=0,
        pale_leaf_expansion_px=0,
        root_trim_px=max(base_settings.root_trim_px, 10),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.78),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def root_strict_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=30, h_max=112, s_min=185, s_max=255, v_min=25),
        min_object_area_px=350,
        max_object_area_px=45000,
        green_dominance_margin=24,
        green_index_min=80,
        leaf_fill_px=2,
        pale_leaf_expansion_px=14,
        root_trim_px=7,
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.86),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def broad_strict_leaf_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    """Use broad HSV limits, then rely on strict green dominance to reject artefacts."""
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=38, h_max=92, s_min=0, s_max=255, v_min=0),
        min_object_area_px=0,
        max_object_area_px=50000,
        green_dominance_margin=78,
        green_index_min=80,
        leaf_fill_px=0,
        pale_leaf_expansion_px=15,
        root_trim_px=max(base_settings.root_trim_px, 10),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.86),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def contrast_strict_leaf_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    """Prefer compact, strongly green leaves when the medium contrast is already good."""
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=25, h_max=120, s_min=85, s_max=255, v_min=25),
        min_object_area_px=240,
        max_object_area_px=65000,
        green_dominance_margin=80,
        green_index_min=80,
        leaf_fill_px=4,
        pale_leaf_expansion_px=22,
        root_trim_px=max(base_settings.root_trim_px, 10),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.78),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def small_pale_core_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    """Conservative mode for weak plants where only saturated leaf cores are reliable."""
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=43, h_max=82, s_min=231, s_max=255, v_min=57),
        min_object_area_px=1454,
        max_object_area_px=120000,
        green_dominance_margin=10,
        green_index_min=46,
        leaf_fill_px=2,
        pale_leaf_expansion_px=28,
        root_trim_px=max(base_settings.root_trim_px, 10),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.78),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def pale_leaf_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=25, h_max=120, s_min=85, s_max=255, v_min=25),
        min_object_area_px=240,
        max_object_area_px=65000,
        green_dominance_margin=12,
        green_index_min=45,
        leaf_fill_px=4,
        pale_leaf_expansion_px=22,
        root_trim_px=max(base_settings.root_trim_px, 3),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.86),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def pale_leaf_base_root_settings(
    base_settings: AnalysisSettings,
    manual_petri_circle: tuple[int, int, int] | None,
) -> AnalysisSettings:
    """Recover grey-green leaf bases while keeping root-like appendages constrained."""
    return AnalysisSettings(
        thresholds=HSVThresholds(h_min=22, h_max=125, s_min=38, s_max=255, v_min=20),
        min_object_area_px=160,
        max_object_area_px=70000,
        green_dominance_margin=0,
        green_index_min=-5,
        leaf_fill_px=1,
        pale_leaf_expansion_px=32,
        root_trim_px=max(base_settings.root_trim_px, 8),
        inner_dish_factor=min(base_settings.inner_dish_factor, 0.86),
        morphology_kernel_size=base_settings.morphology_kernel_size,
        manual_petri_circle=manual_petri_circle,
        excluded_component_points=base_settings.excluded_component_points,
    )


def percentile(values: np.ndarray, percent: float) -> float:
    return float(np.percentile(values, percent))


def clamp_int(value: float, minimum: int, maximum: int) -> int:
    return int(max(minimum, min(maximum, round(value))))
