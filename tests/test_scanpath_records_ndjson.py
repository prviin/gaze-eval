from __future__ import annotations

import pandas as pd

from gaze_eval.scanpath.evaluate_records import evaluate_scanpath_records
from gaze_eval.scanpath.io import read_scanpath_ndjson
from gaze_eval.scanpath.records import Fixation, ScanpathRecord


def test_evaluate_scanpath_records_with_random_like_data() -> None:
    human_records = [
        ScanpathRecord(
            schema_version="gaze-eval-scanpath-v1",
            source="human",
            dataset="debug",
            image_id="img_001",
            trial_id="human_s01_img001",
            subject_id="s01",
            coordinate_system={
                "type": "normalized",
                "x_range": [0, 1],
                "y_range": [0, 1],
                "origin": "top_left",
            },
            scanpath=[
                Fixation(
                    fixation_index=0, timestamp=0.0, x=0.10, y=0.20, duration=100.0
                ),
                Fixation(
                    fixation_index=1, timestamp=120.0, x=0.30, y=0.40, duration=150.0
                ),
                Fixation(
                    fixation_index=2, timestamp=300.0, x=0.50, y=0.60, duration=200.0
                ),
            ],
        )
    ]

    predicted_records = [
        ScanpathRecord(
            schema_version="gaze-eval-scanpath-v1",
            source="prediction",
            dataset="debug",
            image_id="img_001",
            trial_id="pred_model_img001",
            prediction_id="pred_001",
            model="dummy_model",
            sampler="dummy_sampler",
            coordinate_system={
                "type": "normalized",
                "x_range": [0, 1],
                "y_range": [0, 1],
                "origin": "top_left",
            },
            scanpath=[
                Fixation(
                    fixation_index=0, timestamp=0.0, x=0.10, y=0.20, duration=100.0
                ),
                Fixation(
                    fixation_index=1, timestamp=120.0, x=0.30, y=0.40, duration=150.0
                ),
                Fixation(
                    fixation_index=2, timestamp=300.0, x=0.50, y=0.60, duration=200.0
                ),
            ],
        )
    ]

    results = evaluate_scanpath_records(
        human_scanpaths=human_records,
        predicted_scanpaths=predicted_records,
        metric_names=["mean_fixation_error", "final_fixation_error"],
    )

    assert isinstance(results, pd.DataFrame)
    assert len(results) == 2

    mean_fixation_error = results.loc[
        results["metric"] == "mean_fixation_error",
        "value",
    ].iloc[0]

    final_fixation_error = results.loc[
        results["metric"] == "final_fixation_error",
        "value",
    ].iloc[0]

    assert mean_fixation_error == 0.0
    assert final_fixation_error == 0.0
