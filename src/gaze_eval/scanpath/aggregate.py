from __future__ import annotations

import pandas as pd


def aggregate_scanpath_results(results: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate raw scanpath metric results.

    The raw results contain one row per prediction-subject-metric comparison.

    This function aggregates across human subjects for each:
        image_id, prediction_id, model, sampler, metric

    Args:
        results:
            Raw output from evaluate_scanpaths().

    Returns:
        Aggregated DataFrame with mean, std, median, min, max,
        n_subjects, and n_valid.
    """
    required_columns = {
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

    missing = required_columns - set(results.columns)
    if missing:
        raise ValueError(f"results is missing required columns: {missing}")

    grouped = results.groupby(
        [
            "image_id",
            "prediction_id",
            "model",
            "sampler",
            "metric",
            "category",
            "direction",
        ],
        as_index=False,
    )

    return grouped.agg(
        mean=("value", "mean"),
        std=("value", "std"),
        median=("value", "median"),
        min=("value", "min"),
        max=("value", "max"),
        n_subjects=("subject_id", "nunique"),
        n_valid=("value", "count"),
    )
