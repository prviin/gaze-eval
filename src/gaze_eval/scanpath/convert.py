from __future__ import annotations

from pathlib import Path

import pandas as pd

from gaze_eval.scanpath.io import write_scanpath_ndjson
from gaze_eval.scanpath.records import Fixation, ScanpathRecord


DEFAULT_COORDINATE_SYSTEM = {
    "type": "normalized",
    "x_range": [0, 1],
    "y_range": [0, 1],
    "origin": "top_left",
}


def human_dataframe_to_records(
    dataframe: pd.DataFrame,
    *,
    dataset: str = "debug",
    schema_version: str = "gaze-eval-scanpath-v1",
) -> list[ScanpathRecord]:
    required_columns = {
        "image_id",
        "subject_id",
        "fixation_index",
        "x",
        "y",
        "duration",
    }

    missing = required_columns - set(dataframe.columns)
    if missing:
        raise ValueError(f"human dataframe is missing columns: {sorted(missing)}")

    records: list[ScanpathRecord] = []

    group_columns = ["image_id", "subject_id"]

    for (image_id, subject_id), group in dataframe.groupby(group_columns):
        group = group.sort_values("fixation_index")

        record_dataset = (
            str(group["dataset"].iloc[0]) if "dataset" in group.columns else dataset
        )

        fixations = [
            Fixation(
                fixation_index=int(row["fixation_index"]),
                timestamp=(
                    float(row["timestamp"])
                    if "timestamp" in group.columns and pd.notna(row["timestamp"])
                    else None
                ),
                x=float(row["x"]),
                y=float(row["y"]),
                duration=float(row["duration"]),
            )
            for _, row in group.iterrows()
        ]

        records.append(
            ScanpathRecord(
                schema_version=schema_version,
                source="human",
                dataset=record_dataset,
                image_id=str(image_id),
                trial_id=f"{subject_id}_{image_id}",
                subject_id=str(subject_id),
                coordinate_system=DEFAULT_COORDINATE_SYSTEM,
                time_unit="ms",
                duration_unit="ms",
                scanpath=fixations,
            )
        )

    return records


def prediction_dataframe_to_records(
    dataframe: pd.DataFrame,
    *,
    dataset: str = "debug",
    schema_version: str = "gaze-eval-scanpath-v1",
) -> list[ScanpathRecord]:
    required_columns = {
        "image_id",
        "prediction_id",
        "model",
        "sampler",
        "fixation_index",
        "x",
        "y",
        "duration",
    }

    missing = required_columns - set(dataframe.columns)
    if missing:
        raise ValueError(f"prediction dataframe is missing columns: {sorted(missing)}")

    records: list[ScanpathRecord] = []

    group_columns = ["image_id", "prediction_id", "model", "sampler"]

    for group_values, group in dataframe.groupby(group_columns):
        image_id, prediction_id, model, sampler = group_values
        group = group.sort_values("fixation_index")

        record_dataset = (
            str(group["dataset"].iloc[0]) if "dataset" in group.columns else dataset
        )

        fixations = [
            Fixation(
                fixation_index=int(row["fixation_index"]),
                timestamp=(
                    float(row["timestamp"])
                    if "timestamp" in group.columns and pd.notna(row["timestamp"])
                    else None
                ),
                x=float(row["x"]),
                y=float(row["y"]),
                duration=float(row["duration"]),
            )
            for _, row in group.iterrows()
        ]

        records.append(
            ScanpathRecord(
                schema_version=schema_version,
                source="prediction",
                dataset=record_dataset,
                image_id=str(image_id),
                trial_id=str(prediction_id),
                prediction_id=str(prediction_id),
                model=str(model),
                sampler=str(sampler),
                coordinate_system=DEFAULT_COORDINATE_SYSTEM,
                time_unit="ms",
                duration_unit="ms",
                scanpath=fixations,
            )
        )

    return records


def human_records_to_prediction_records(
    records: list[ScanpathRecord],
    *,
    model_name: str = "human",
    sampler_name: str = "human_subject",
) -> list[ScanpathRecord]:
    prediction_records: list[ScanpathRecord] = []

    for record in records:
        if record.source != "human":
            raise ValueError("all input records must have source='human'")

        if record.subject_id is None:
            raise ValueError("human record is missing subject_id")

        prediction_records.append(
            ScanpathRecord(
                schema_version=record.schema_version,
                source="prediction",
                dataset=record.dataset,
                image_id=record.image_id,
                trial_id=f"human_pred_{record.subject_id}_{record.image_id}",
                prediction_id=f"{record.image_id}_{record.subject_id}",
                model=model_name,
                sampler=sampler_name,
                split=record.split,
                task_id=record.task_id,
                condition=record.condition,
                session_id=record.session_id,
                run_id=record.run_id,
                stimulus=record.stimulus,
                coordinate_system=record.coordinate_system,
                time_unit=record.time_unit,
                duration_unit=record.duration_unit,
                scanpath=record.scanpath,
                metadata={
                    **record.metadata,
                    "original_subject_id": record.subject_id,
                },
            )
        )

    return prediction_records


def convert_human_csv_to_ndjson(
    csv_path: str | Path,
    ndjson_path: str | Path,
    *,
    dataset: str = "debug",
) -> None:
    dataframe = pd.read_csv(csv_path)
    records = human_dataframe_to_records(dataframe, dataset=dataset)
    write_scanpath_ndjson(records, ndjson_path)


def convert_prediction_csv_to_ndjson(
    csv_path: str | Path,
    ndjson_path: str | Path,
    *,
    dataset: str = "debug",
) -> None:
    dataframe = pd.read_csv(csv_path)
    records = prediction_dataframe_to_records(dataframe, dataset=dataset)
    write_scanpath_ndjson(records, ndjson_path)
