from __future__ import annotations

from pathlib import Path

import pandas as pd

from gaze_eval.scanpath.convert import (
    human_dataframe_to_records,
    human_records_to_prediction_records,
    prediction_dataframe_to_records,
)
from gaze_eval.scanpath.evaluate_records import evaluate_scanpath_records


def test_human_dataframe_to_records_from_legacy_csv() -> None:
    dataframe = pd.read_csv("tests/data/debug/human_scanpaths.csv")

    records = human_dataframe_to_records(dataframe, dataset="debug")

    assert len(records) > 0
    assert records[0].source == "human"
    assert records[0].subject_id is not None
    assert len(records[0].scanpath) > 0


def test_prediction_dataframe_to_records_from_legacy_csv() -> None:
    dataframe = pd.read_csv("tests/data/debug/pred_good.csv")

    records = prediction_dataframe_to_records(dataframe, dataset="debug")

    assert len(records) > 0
    assert records[0].source == "prediction"
    assert records[0].prediction_id is not None
    assert records[0].model is not None
    assert records[0].sampler is not None
    assert len(records[0].scanpath) > 0


def test_human_records_to_prediction_records() -> None:
    dataframe = pd.read_csv("tests/data/debug/human_scanpaths.csv")

    human_records = human_dataframe_to_records(dataframe, dataset="debug")
    prediction_records = human_records_to_prediction_records(human_records)

    assert len(prediction_records) == len(human_records)

    assert prediction_records[0].source == "prediction"
    assert prediction_records[0].model == "human"
    assert prediction_records[0].sampler == "human_subject"
    assert "original_subject_id" in prediction_records[0].metadata


def test_evaluate_legacy_csv_after_record_conversion() -> None:
    human_df = pd.read_csv("tests/data/debug/human_scanpaths.csv")
    pred_df = pd.read_csv("tests/data/debug/pred_good.csv")

    human_records = human_dataframe_to_records(human_df, dataset="debug")
    pred_records = prediction_dataframe_to_records(pred_df, dataset="debug")

    results = evaluate_scanpath_records(
        human_scanpaths=human_records,
        predicted_scanpaths=pred_records,
        metric_names=[
            "mean_fixation_error",
            "final_fixation_error",
            "dtw",
        ],
    )

    assert not results.empty
    assert set(results["metric"]) == {
        "mean_fixation_error",
        "final_fixation_error",
        "dtw",
    }
