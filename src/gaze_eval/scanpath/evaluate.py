from __future__ import annotations

from typing import Iterable

import pandas as pd

from gaze_eval.scanpath.metrics import SCANPATH_METRICS


def _required_columns_exist(
    dataframe: pd.DataFrame,
    required_columns: set[str],
    name: str,
) -> None:
    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def evaluate_scanpaths(
    human_scanpaths: pd.DataFrame,
    predicted_scanpaths: pd.DataFrame,
    metric_names: Iterable[str] | None = None,
) -> pd.DataFrame:
    """
    Evaluate predicted scanpaths against human scanpaths.

    Each predicted scanpath is compared with each human subject scanpath
    for the same image.

    Args:
        human_scanpaths:
            DataFrame with columns:
            image_id, subject_id, fixation_index, x, y, duration

        predicted_scanpaths:
            DataFrame with columns:
            image_id, prediction_id, model, sampler, fixation_index, x, y, duration

        metric_names:
            List of metric names to compute. If None, all registered metrics are used.

    Returns:
        Tidy DataFrame with one row per:
            image_id, prediction_id, subject_id, metric
    """
    _required_columns_exist(
        human_scanpaths,
        {"image_id", "subject_id", "fixation_index", "x", "y"},
        "human_scanpaths",
    )

    _required_columns_exist(
        predicted_scanpaths,
        {"image_id", "prediction_id", "model", "sampler", "fixation_index", "x", "y"},
        "predicted_scanpaths",
    )

    if metric_names is None:
        metric_names = list(SCANPATH_METRICS)

    metric_names = list(metric_names)

    unknown_metrics = set(metric_names) - set(SCANPATH_METRICS)
    if unknown_metrics:
        raise ValueError(f"Unknown metrics: {unknown_metrics}")

    rows: list[dict[str, object]] = []

    prediction_group_columns = ["image_id", "prediction_id", "model", "sampler"]

    for (
        image_id,
        prediction_id,
        model,
        sampler,
    ), pred_group in predicted_scanpaths.groupby(prediction_group_columns):
        human_for_image = human_scanpaths[human_scanpaths["image_id"] == image_id]

        if human_for_image.empty:
            continue

        for subject_id, human_group in human_for_image.groupby("subject_id"):
            for metric_name in metric_names:
                metric = SCANPATH_METRICS[metric_name]

                try:
                    value = metric.function(pred_group, human_group)
                except Exception:
                    value = float("nan")

                rows.append(
                    {
                        "image_id": image_id,
                        "prediction_id": prediction_id,
                        "subject_id": subject_id,
                        "model": model,
                        "sampler": sampler,
                        "metric": metric.name,
                        "category": metric.category,
                        "direction": metric.direction,
                        "value": value,
                    }
                )

    return pd.DataFrame(rows)
