from __future__ import annotations

from pathlib import Path

import pandas as pd

from gaze_eval.data.pairs import (
    make_different_image_human_pairs,
    make_same_image_human_pairs,
)
from gaze_eval.scanpath.metrics import SCANPATH_METRICS


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "tests" / "data" / "debug" / "multi_image_human_scanpaths.csv"
OUTPUT_DIR = ROOT / "results" / "metrics" / "debug"


LOWER_IS_BETTER = {
    "mean_fixation_error",
    "final_fixation_error",
    "mean_saccade_amplitude_error",
    "mean_saccade_angle_error",
    "mean_duration_error",
    "dtw",
    "frechet",
    "hausdorff",
    "levenshtein",
    "eyenalysis",
    "tde",
    "scaled_tde",
}

HIGHER_IS_BETTER = {
    "duration_correlation",
    "scanmatch",
    "needleman_wunsch",
    "aoi_transition_similarity",
    "sequence_score",
    "mannan_distance",
}

DESCRIPTIVE = {
    "number_of_fixations",
    "aoi_transition_count",
    "recurrence",
    "determinism",
    "laminarity",
    "corm",
}


METRIC_NAMES = [
    "mean_fixation_error",
    "final_fixation_error",
    "mean_saccade_amplitude_error",
    "mean_saccade_angle_error",
    "mean_duration_error",
    "duration_correlation",
    "dtw",
    "frechet",
    "hausdorff",
    "scanmatch",
    "levenshtein",
    "needleman_wunsch",
    "aoi_transition_similarity",
    "sequence_score",
    "eyenalysis",
    "mannan_distance",
    "recurrence",
    "determinism",
    "laminarity",
    "corm",
    "tde",
    "scaled_tde",
    "number_of_fixations",
    "aoi_transition_count",
]


def _get_scanpath(
    scanpaths: pd.DataFrame,
    image_id: str,
    subject_id: str,
) -> pd.DataFrame:
    return scanpaths[
        (scanpaths["image_id"] == image_id) & (scanpaths["subject_id"] == subject_id)
    ]


def evaluate_pairs(
    scanpaths: pd.DataFrame,
    pairs: pd.DataFrame,
    metric_names: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for _, pair in pairs.iterrows():
        pred = _get_scanpath(
            scanpaths,
            image_id=pair["prediction_image_id"],
            subject_id=pair["prediction_subject_id"],
        )
        gt = _get_scanpath(
            scanpaths,
            image_id=pair["groundtruth_image_id"],
            subject_id=pair["groundtruth_subject_id"],
        )

        for metric_name in metric_names:
            metric = SCANPATH_METRICS[metric_name]

            try:
                value = metric.function(pred, gt)
            except Exception:
                value = float("nan")

            rows.append(
                {
                    "pair_type": pair["pair_type"],
                    "prediction_image_id": pair["prediction_image_id"],
                    "prediction_subject_id": pair["prediction_subject_id"],
                    "groundtruth_image_id": pair["groundtruth_image_id"],
                    "groundtruth_subject_id": pair["groundtruth_subject_id"],
                    "metric": metric.name,
                    "category": metric.category,
                    "direction": metric.direction,
                    "value": value,
                }
            )

    return pd.DataFrame(rows)


def classify_metric(
    metric: str,
    same_image_mean: float,
    different_image_mean: float,
) -> str:
    if pd.isna(same_image_mean) or pd.isna(different_image_mean):
        return "undefined"

    if metric in LOWER_IS_BETTER:
        if same_image_mean < different_image_mean:
            return "expected_same_image_better"
        return "unexpected"

    if metric in HIGHER_IS_BETTER:
        if same_image_mean > different_image_mean:
            return "expected_same_image_better"
        return "unexpected"

    if metric in DESCRIPTIVE:
        return "descriptive_no_strict_order"

    return "unknown_direction"


def summarize(raw: pd.DataFrame) -> pd.DataFrame:
    summary = raw.groupby(
        ["metric", "category", "direction", "pair_type"], as_index=False
    ).agg(
        mean=("value", "mean"),
        std=("value", "std"),
        median=("value", "median"),
        min=("value", "min"),
        max=("value", "max"),
        n_pairs=("value", "count"),
    )

    compact = summary.pivot_table(
        index=["metric", "category", "direction"],
        columns="pair_type",
        values="mean",
        aggfunc="first",
    ).reset_index()

    compact.columns.name = None

    compact["conclusion"] = compact.apply(
        lambda row: classify_metric(
            metric=row["metric"],
            same_image_mean=row.get("same_image", float("nan")),
            different_image_mean=row.get("different_image", float("nan")),
        ),
        axis=1,
    )

    return compact


def main() -> None:
    scanpaths = pd.read_csv(DATA_PATH)

    same_pairs = make_same_image_human_pairs(scanpaths)
    different_pairs = make_different_image_human_pairs(scanpaths)
    pairs = pd.concat([same_pairs, different_pairs], ignore_index=True)

    raw = evaluate_pairs(
        scanpaths=scanpaths,
        pairs=pairs,
        metric_names=METRIC_NAMES,
    )

    summary = summarize(raw)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = OUTPUT_DIR / "dummy_same_vs_different_image_raw.csv"
    summary_path = OUTPUT_DIR / "dummy_same_vs_different_image_summary.csv"

    raw.to_csv(raw_path, index=False)
    summary.to_csv(summary_path, index=False)

    print("\nSame-image vs different-image summary")
    print("=" * 80)
    print(summary.to_string(index=False))

    print("\nConclusion counts")
    print("=" * 80)
    print(summary["conclusion"].value_counts().to_string())

    print(f"\nSaved raw results to: {raw_path}")
    print(f"Saved summary to: {summary_path}")


if __name__ == "__main__":
    main()
