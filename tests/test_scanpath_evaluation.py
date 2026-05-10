from pathlib import Path

import pandas as pd

from gaze_eval.scanpath.aggregate import aggregate_scanpath_results
from gaze_eval.scanpath.evaluate import evaluate_scanpaths


DATA_DIR = Path(__file__).parent / "data" / "debug"


def test_evaluate_scanpaths_returns_expected_rows() -> None:
    human = pd.read_csv(DATA_DIR / "human_scanpaths.csv")
    pred = pd.read_csv(DATA_DIR / "pred_good.csv")

    metric_names = [
        "mean_fixation_error",
        "dtw",
        "sequence_score",
    ]

    results = evaluate_scanpaths(
        human_scanpaths=human,
        predicted_scanpaths=pred,
        metric_names=metric_names,
    )

    # 1 prediction x 2 human subjects x 3 metrics = 6 rows
    assert len(results) == 6

    expected_columns = {
        "image_id",
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
    assert set(results["metric"]) == set(metric_names)


def test_aggregate_scanpath_results_returns_expected_rows() -> None:
    human = pd.read_csv(DATA_DIR / "human_scanpaths.csv")
    pred = pd.read_csv(DATA_DIR / "pred_good.csv")

    metric_names = [
        "mean_fixation_error",
        "dtw",
        "sequence_score",
    ]

    results = evaluate_scanpaths(
        human_scanpaths=human,
        predicted_scanpaths=pred,
        metric_names=metric_names,
    )

    summary = aggregate_scanpath_results(results)

    # 1 prediction x 3 metrics = 3 summary rows
    assert len(summary) == 3

    expected_columns = {
        "image_id",
        "prediction_id",
        "model",
        "sampler",
        "metric",
        "category",
        "direction",
        "mean",
        "std",
        "median",
        "min",
        "max",
        "n_subjects",
        "n_valid",
    }

    assert expected_columns.issubset(summary.columns)
    assert set(summary["metric"]) == set(metric_names)
    assert all(summary["n_subjects"] == 2)
