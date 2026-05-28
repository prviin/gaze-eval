from __future__ import annotations

from pathlib import Path

import pandas as pd

from gaze_eval.scanpath.evaluate_records import evaluate_scanpath_records
from gaze_eval.scanpath.io import read_scanpath_ndjson
from gaze_eval.scanpath.metrics import SCANPATH_METRICS


def test_all_registered_metrics_run_on_ndjson_debug_data() -> None:
    data_dir = Path("tests/data/debug")

    human_records = read_scanpath_ndjson(data_dir / "human_scanpaths.ndjson")
    pred_records = read_scanpath_ndjson(data_dir / "pred_scanpaths.ndjson")

    results = evaluate_scanpath_records(
        human_scanpaths=human_records,
        predicted_scanpaths=pred_records,
        metric_names=list(SCANPATH_METRICS),
    )

    assert isinstance(results, pd.DataFrame)
    assert not results.empty

    evaluated_metrics = set(results["metric"])
    registered_metrics = {metric.name for metric in SCANPATH_METRICS.values()}

    assert evaluated_metrics == registered_metrics

    assert "value" in results.columns
