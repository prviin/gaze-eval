from __future__ import annotations

from pathlib import Path

from gaze_eval.scanpath.evaluate_records import evaluate_scanpath_records
from gaze_eval.scanpath.io import read_scanpath_ndjson


def main() -> None:
    data_dir = Path("tests/data/debug")

    human_records = read_scanpath_ndjson(data_dir / "human_scanpaths.ndjson")
    pred_records = read_scanpath_ndjson(data_dir / "pred_scanpaths.ndjson")

    results = evaluate_scanpath_records(
        human_scanpaths=human_records,
        predicted_scanpaths=pred_records,
        metric_names=[
            "mean_fixation_error",
            "final_fixation_error",
            "mean_duration_error",
            "duration_correlation",
            "dtw",
        ],
    )

    print(results.to_string(index=False))


if __name__ == "__main__":
    main()
