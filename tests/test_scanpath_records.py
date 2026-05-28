from __future__ import annotations

from pathlib import Path

from gaze_eval.scanpath.evaluate_records import evaluate_scanpath_records
from gaze_eval.scanpath.io import read_scanpath_ndjson


def test_read_scanpath_ndjson_files() -> None:
    data_dir = Path("tests/data/debug")

    human_records = read_scanpath_ndjson(data_dir / "human_scanpaths.ndjson")
    pred_records = read_scanpath_ndjson(data_dir / "pred_scanpaths.ndjson")

    assert len(human_records) > 0
    assert len(pred_records) > 0

    assert human_records[0].source == "human"
    assert pred_records[0].source == "prediction"

    assert human_records[0].scanpath[0].timestamp is not None
    assert pred_records[0].scanpath[0].timestamp is not None


def test_evaluate_scanpath_records_from_ndjson() -> None:
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
        ],
    )

    assert not results.empty

    assert set(results["metric"]) == {
        "mean_fixation_error",
        "final_fixation_error",
        "mean_duration_error",
    }

    expected_columns = {
        "dataset",
        "image_id",
        "trial_id",
        "prediction_id",
        "subject_id",
        "model",
        "sampler",
        "metric",
        "category",
        "direction",
        "value",
    }

    assert expected_columns.issubset(results.columns)
    assert results.loc[results["metric"] == "mean_fixation_error", "value"].iloc[0] > 0
    assert results.loc[results["metric"] == "mean_duration_error", "value"].iloc[0] > 0
    assert (
        results.loc[results["metric"] == "final_fixation_error", "value"].iloc[0] == 0
    )
