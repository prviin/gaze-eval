from __future__ import annotations

from pathlib import Path

from gaze_eval.scanpath.convert import human_records_to_prediction_records
from gaze_eval.scanpath.evaluate_records import evaluate_scanpath_records
from gaze_eval.scanpath.io import read_scanpath_ndjson


def main() -> None:
    human_records = read_scanpath_ndjson(
        Path("tests/data/debug/human_scanpaths.ndjson")
    )

    human_as_predictions = human_records_to_prediction_records(human_records)

    results = evaluate_scanpath_records(
        human_scanpaths=human_records,
        predicted_scanpaths=human_as_predictions,
        metric_names=[
            "mean_fixation_error",
            "final_fixation_error",
            "dtw",
        ],
        exclude_self_comparisons=True,
    )

    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
