from __future__ import annotations

from pathlib import Path

import pandas as pd

from gaze_eval.data.convert import human_scanpaths_to_predictions
from gaze_eval.data.splits import split_human_scanpaths_by_subject
from gaze_eval.scanpath.aggregate import aggregate_scanpath_results
from gaze_eval.scanpath.evaluate import evaluate_scanpaths


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "tests" / "data" / "debug"
OUTPUT_DIR = ROOT / "results" / "metrics" / "debug"


def main() -> None:
    human = pd.read_csv(DATA_DIR / "human_scanpaths.csv")

    prediction_part, groundtruth_part = split_human_scanpaths_by_subject(
        human,
        split_ratio=0.5,
        seed=42,
    )

    pseudo_predictions = human_scanpaths_to_predictions(
        prediction_part,
        model_name="human_reference",
        sampler_name="subject_split",
    )

    metric_names = [
        "mean_fixation_error",
        "dtw",
        "frechet",
        "hausdorff",
        "scanmatch",
        "levenshtein",
        "sequence_score",
        "eyenalysis",
        "mannan_distance",
        "tde",
        "scaled_tde",
    ]

    raw = evaluate_scanpaths(
        human_scanpaths=groundtruth_part,
        predicted_scanpaths=pseudo_predictions,
        metric_names=metric_names,
    )

    summary = aggregate_scanpath_results(raw)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = OUTPUT_DIR / "dummy_human_vs_human_raw.csv"
    summary_path = OUTPUT_DIR / "dummy_human_vs_human_summary.csv"

    raw.to_csv(raw_path, index=False)
    summary.to_csv(summary_path, index=False)

    print("Human group-vs-human group raw results:")
    print(raw)

    print("\nSummary:")
    print(summary)

    print(f"\nSaved raw results to: {raw_path}")
    print(f"Saved summary to: {summary_path}")


if __name__ == "__main__":
    main()
