from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gaze_eval.scanpath.records import Fixation, ScanpathRecord


def read_scanpath_ndjson(path: str | Path) -> list[ScanpathRecord]:
    records: list[ScanpathRecord] = []

    with Path(path).open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            data = json.loads(line)
            records.append(_dict_to_scanpath_record(data, line_number=line_number))

    return records


def write_scanpath_ndjson(
    records: list[ScanpathRecord],
    path: str | Path,
) -> None:
    with Path(path).open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(_scanpath_record_to_dict(record), ensure_ascii=False))
            file.write("\n")


def _dict_to_scanpath_record(
    data: dict[str, Any],
    *,
    line_number: int,
) -> ScanpathRecord:
    required_keys = {
        "schema_version",
        "source",
        "dataset",
        "image_id",
        "trial_id",
        "scanpath",
    }

    missing = required_keys - set(data)
    if missing:
        raise ValueError(
            f"Line {line_number}: missing required keys: {sorted(missing)}"
        )

    source = data["source"]
    if source not in {"human", "prediction"}:
        raise ValueError(f"Line {line_number}: source must be 'human' or 'prediction'")

    if source == "human" and "subject_id" not in data:
        raise ValueError(f"Line {line_number}: human record needs subject_id")

    if source == "prediction":
        prediction_required = {"prediction_id", "model", "sampler"}
        missing_prediction = prediction_required - set(data)
        if missing_prediction:
            raise ValueError(
                f"Line {line_number}: prediction record missing "
                f"{sorted(missing_prediction)}"
            )

    fixations = []
    for fixation in data["scanpath"]:
        fixation_required = {"fixation_index", "x", "y", "duration"}
        missing_fixation = fixation_required - set(fixation)

        if missing_fixation:
            raise ValueError(
                f"Line {line_number}: fixation missing {sorted(missing_fixation)}"
            )

        fixations.append(
            Fixation(
                fixation_index=int(fixation["fixation_index"]),
                timestamp=(
                    float(fixation["timestamp"])
                    if fixation.get("timestamp") is not None
                    else None
                ),
                x=float(fixation["x"]),
                y=float(fixation["y"]),
                duration=float(fixation["duration"]),
            )
        )

    known_keys = {
        "schema_version",
        "source",
        "dataset",
        "image_id",
        "trial_id",
        "subject_id",
        "prediction_id",
        "model",
        "sampler",
        "split",
        "task_id",
        "condition",
        "session_id",
        "run_id",
        "stimulus",
        "coordinate_system",
        "time_unit",
        "duration_unit",
        "scanpath",
    }

    metadata = {key: value for key, value in data.items() if key not in known_keys}

    return ScanpathRecord(
        schema_version=data["schema_version"],
        source=source,
        dataset=data["dataset"],
        image_id=data["image_id"],
        trial_id=data["trial_id"],
        subject_id=data.get("subject_id"),
        prediction_id=data.get("prediction_id"),
        model=data.get("model"),
        sampler=data.get("sampler"),
        split=data.get("split"),
        task_id=data.get("task_id"),
        condition=data.get("condition"),
        session_id=data.get("session_id"),
        run_id=data.get("run_id"),
        stimulus=data.get("stimulus", {}),
        coordinate_system=data.get(
            "coordinate_system",
            {
                "type": "normalized",
                "x_range": [0, 1],
                "y_range": [0, 1],
                "origin": "top_left",
            },
        ),
        time_unit=data.get("time_unit", "ms"),
        duration_unit=data.get("duration_unit", "ms"),
        scanpath=fixations,
        metadata=metadata,
    )


def _scanpath_record_to_dict(record: ScanpathRecord) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": record.schema_version,
        "source": record.source,
        "dataset": record.dataset,
        "image_id": record.image_id,
        "trial_id": record.trial_id,
        "coordinate_system": record.coordinate_system,
        "time_unit": record.time_unit,
        "duration_unit": record.duration_unit,
        "scanpath": [
            {
                "fixation_index": fixation.fixation_index,
                "timestamp": fixation.timestamp,
                "x": fixation.x,
                "y": fixation.y,
                "duration": fixation.duration,
            }
            for fixation in record.scanpath
        ],
    }

    optional_fields = [
        "subject_id",
        "prediction_id",
        "model",
        "sampler",
        "split",
        "task_id",
        "condition",
        "session_id",
        "run_id",
    ]

    for field_name in optional_fields:
        value = getattr(record, field_name)
        if value is not None:
            data[field_name] = value

    if record.stimulus:
        data["stimulus"] = record.stimulus

    data.update(record.metadata)

    return data
