from __future__ import annotations

import pandas as pd


def human_scanpaths_to_predictions(
    scanpaths: pd.DataFrame,
    model_name: str = "human",
    sampler_name: str = "human_subject",
) -> pd.DataFrame:
    """
    Convert human scanpaths into predicted-scanpath format.

    This is useful for human group-vs-human group evaluation.
    """
    required_columns = {
        "image_id",
        "subject_id",
        "fixation_index",
        "x",
        "y",
        "duration",
    }

    missing = required_columns - set(scanpaths.columns)
    if missing:
        raise ValueError(f"scanpaths is missing required columns: {missing}")

    predictions = scanpaths.copy()

    predictions["prediction_id"] = (
        predictions["image_id"].astype(str)
        + "_"
        + predictions["subject_id"].astype(str)
    )

    predictions["model"] = model_name
    predictions["sampler"] = sampler_name

    columns = [
        "image_id",
        "prediction_id",
        "model",
        "sampler",
        "fixation_index",
        "x",
        "y",
        "duration",
    ]

    if "dataset" in predictions.columns:
        columns = ["dataset"] + columns

    return predictions[columns]
