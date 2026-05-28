from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from gaze_eval.scanpath.evaluate_records import _record_to_metric_dataframe
from gaze_eval.scanpath.metrics import SCANPATH_METRICS
from gaze_eval.scanpath.records import ScanpathRecord
from tqdm.auto import tqdm


def evaluate_human_pair_sample(
    records: list[ScanpathRecord],
    pairs: pd.DataFrame,
    metric_names: Iterable[str] | None = None,
) -> pd.DataFrame:
    """
    Evaluate a saved human-human pair sample.

    This function is deterministic as long as the input pair CSV is fixed.
    """
    if metric_names is None:
        metric_names = list(SCANPATH_METRICS)

    metric_names = list(metric_names)

    unknown_metrics = set(metric_names) - set(SCANPATH_METRICS)
    if unknown_metrics:
        raise ValueError(f"Unknown metrics: {unknown_metrics}")

    record_index = build_record_index(records)

    rows: list[dict[str, object]] = []

    for _, pair in tqdm(
        pairs.iterrows(),
        total=len(pairs),
        desc="Evaluating pair sample",
        unit="pair",
    ):
        record_a = record_index[
            (
                str(pair["trial_id_a"]),
                str(pair["subject_id_a"]),
                str(pair["image_id_a"]),
            )
        ]

        record_b = record_index[
            (
                str(pair["trial_id_b"]),
                str(pair["subject_id_b"]),
                str(pair["image_id_b"]),
            )
        ]

        df_a = _record_to_metric_dataframe(record_a)
        df_b = _record_to_metric_dataframe(record_b)

        for metric_name in metric_names:
            metric = SCANPATH_METRICS[metric_name]

            try:
                value = metric.function(df_a, df_b)
            except Exception:
                value = float("nan")

            rows.append(
                {
                    "pair_id": pair["pair_id"],
                    "comparison_type": pair["comparison_type"],
                    "image_id_a": pair["image_id_a"],
                    "subject_id_a": pair["subject_id_a"],
                    "trial_id_a": pair["trial_id_a"],
                    "category_a": pair["category_a"],
                    "image_id_b": pair["image_id_b"],
                    "subject_id_b": pair["subject_id_b"],
                    "trial_id_b": pair["trial_id_b"],
                    "category_b": pair["category_b"],
                    "metric": metric.name,
                    "category": metric.category,
                    "direction": metric.direction,
                    "value": value,
                }
            )

    return pd.DataFrame(rows)


def build_record_index(
    records: list[ScanpathRecord],
) -> dict[tuple[str, str, str], ScanpathRecord]:
    index = {}

    for record in records:
        if record.subject_id is None:
            raise ValueError("record is missing subject_id")

        key = (
            str(record.trial_id),
            str(record.subject_id),
            str(record.image_id),
        )

        if key in index:
            raise ValueError(f"duplicate record key: {key}")

        index[key] = record

    return index
