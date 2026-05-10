from __future__ import annotations

from pathlib import Path

import pandas as pd

from gaze_eval.scanpath.aggregate import aggregate_scanpath_results
from gaze_eval.scanpath.evaluate import evaluate_scanpaths


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "tests" / "data" / "debug"
OUTPUT_DIR = ROOT / "results" / "metrics" / "debug"


def run_case(case_name: str, pred_filename: str) -> None:
    human_path = DATA_DIR / "human_scanpaths.csv"
    pred_path = DATA_DIR / pred_filename

    human_scanpaths = pd.read_csv(human_path)
    predicted_scanpaths = pd.read_csv(pred_path)

    metric_names = [
        # Point-wise geometric
        "mean_fixation_error",
        "final_fixation_error",
        "mean_saccade_amplitude_error",
        "mean_saccade_angle_error",
        # Temporal
        "mean_duration_error",
        "duration_correlation",
        # Alignment
        "dtw",
        "frechet",
        "hausdorff",
        # MultiMatch
        "multimatch_shape",
        "multimatch_direction",
        "multimatch_length",
        "multimatch_position",
        "multimatch_duration",
        # Symbolic / AOI
        "scanmatch",
        "levenshtein",
        "needleman_wunsch",
        "aoi_transition_similarity",
        "sequence_score",
        # Scanpath statistics
        "number_of_fixations",
        "aoi_transition_count",
        # Spatial set-based
        "eyenalysis",
        "mannan_distance",
        # Recurrence
        "recurrence",
        "determinism",
        "laminarity",
        "corm",
        # Temporal embedding
        "tde",
        "scaled_tde",
    ]

    results = evaluate_scanpaths(
        human_scanpaths=human_scanpaths,
        predicted_scanpaths=predicted_scanpaths,
        metric_names=metric_names,
    )

    summary = aggregate_scanpath_results(results)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_output_path = OUTPUT_DIR / f"{case_name}_scanpath_metrics.csv"
    summary_output_path = OUTPUT_DIR / f"{case_name}_scanpath_metrics_summary.csv"

    results.to_csv(raw_output_path, index=False)
    summary.to_csv(summary_output_path, index=False)

    print("=" * 80)
    print(f"Case: {case_name}")
    print("=" * 80)
    print("\nRaw results:")
    print(results)
    print(f"\nSaved raw results to: {raw_output_path}")

    print("\nSummary:")
    print(summary)
    print(f"\nSaved summary to: {summary_output_path}")


def main() -> None:
    cases = {
        "same": "pred_same.csv",
        "good": "pred_good.csv",
        "bad": "pred_bad.csv",
    }

    for case_name, pred_filename in cases.items():
        run_case(case_name=case_name, pred_filename=pred_filename)


if __name__ == "__main__":
    main()
