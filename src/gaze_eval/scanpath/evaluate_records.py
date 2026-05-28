from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

import pandas as pd

from gaze_eval.scanpath.metrics import SCANPATH_METRICS
from gaze_eval.scanpath.records import ScanpathRecord


def _record_to_metric_dataframe(record: ScanpathRecord) -> pd.DataFrame:
    rows = []

    for fixation in record.scanpath:
        rows.append(
            {
                "fixation_index": fixation.fixation_index,
                "timestamp": fixation.timestamp,
                "x": fixation.x,
                "y": fixation.y,
                "duration": fixation.duration,
            }
        )

    return pd.DataFrame(rows)


def evaluate_scanpath_records(
    human_scanpaths: list[ScanpathRecord],
    predicted_scanpaths: list[ScanpathRecord],
    metric_names: Iterable[str] | None = None,
    *,
    exclude_self_comparisons: bool = False,
) -> pd.DataFrame:
    if metric_names is None:
        metric_names = list(SCANPATH_METRICS)

    metric_names = list(metric_names)

    unknown_metrics = set(metric_names) - set(SCANPATH_METRICS)
    if unknown_metrics:
        raise ValueError(f"Unknown metrics: {unknown_metrics}")

    human_by_image: dict[str, list[ScanpathRecord]] = defaultdict(list)

    for record in human_scanpaths:
        if record.source != "human":
            raise ValueError("human_scanpaths contains a non-human record")

        if record.subject_id is None:
            raise ValueError("human scanpath record is missing subject_id")

        human_by_image[record.image_id].append(record)

    rows: list[dict[str, object]] = []

    for pred_record in predicted_scanpaths:
        if pred_record.source != "prediction":
            raise ValueError("predicted_scanpaths contains a non-prediction record")

        if pred_record.prediction_id is None:
            raise ValueError("prediction record is missing prediction_id")

        if pred_record.model is None:
            raise ValueError("prediction record is missing model")

        if pred_record.sampler is None:
            raise ValueError("prediction record is missing sampler")

        human_records = human_by_image.get(pred_record.image_id, [])

        if not human_records:
            continue

        pred_df = _record_to_metric_dataframe(pred_record)

        for human_record in human_records:
            if exclude_self_comparisons:
                original_subject_id = pred_record.metadata.get("original_subject_id")
                if (
                    original_subject_id is not None
                    and original_subject_id == human_record.subject_id
                ):
                    continue
            gt_df = _record_to_metric_dataframe(human_record)

            for metric_name in metric_names:
                metric = SCANPATH_METRICS[metric_name]

                try:
                    value = metric.function(pred_df, gt_df)
                except Exception:
                    value = float("nan")

                rows.append(
                    {
                        "dataset": pred_record.dataset,
                        "image_id": pred_record.image_id,
                        "trial_id": pred_record.trial_id,
                        "prediction_id": pred_record.prediction_id,
                        "subject_id": human_record.subject_id,
                        "model": pred_record.model,
                        "sampler": pred_record.sampler,
                        "metric": metric.name,
                        "category": metric.category,
                        "direction": metric.direction,
                        "value": value,
                    }
                )

    return pd.DataFrame(rows)
