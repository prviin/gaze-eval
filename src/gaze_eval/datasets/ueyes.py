from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from gaze_eval.scanpath.io import write_scanpath_ndjson
from gaze_eval.scanpath.records import Fixation, ScanpathRecord

from tqdm.auto import tqdm


UEYES_SCHEMA_VERSION = "gaze-eval-scanpath-v1"

DEFAULT_COORDINATE_SYSTEM = {
    "type": "normalized",
    "x_range": [0, 1],
    "y_range": [0, 1],
    "origin": "top_left",
}


def load_ueyes(
    root: str | Path,
    *,
    only_valid_fixations: bool = True,
    max_files: int | None = None,
) -> list[ScanpathRecord]:
    """
    Load UEyes fixation files into gaze-eval ScanpathRecord objects.

    Expected structure:

        UEyes_dataset/
        ├── image_types.csv
        └── eyetracker_logs/
            ├── 00_KH005_fixations.csv
            ├── 18_kh008_fixations.csv
            └── ...

    UEyes fixation columns:
        MEDIA_NAME: image filename
        FPOGX: normalized fixation x
        FPOGY: normalized fixation y
        FPOGS: fixation start time in seconds
        FPOGD: fixation duration in seconds
        FPOGID: fixation id
        FPOGV: fixation validity
    """
    root = Path(root)

    image_types_path = root / "image_types.csv"
    logs_dir = root / "eyetracker_logs"

    if not image_types_path.exists():
        raise FileNotFoundError(f"Could not find {image_types_path}")

    if not logs_dir.exists():
        raise FileNotFoundError(f"Could not find {logs_dir}")

    image_metadata = load_ueyes_image_types(image_types_path)

    fixation_files = iter_ueyes_fixation_files(logs_dir)

    if max_files is not None:
        fixation_files = fixation_files[:max_files]

    records: list[ScanpathRecord] = []

    for fixation_file in tqdm(
        fixation_files,
        desc="Loading UEyes fixation files",
        unit="file",
    ):
        subject_id = parse_subject_id_from_filename(fixation_file.name)

        dataframe = pd.read_csv(fixation_file)
        file_records = ueyes_fixation_dataframe_to_records(
            dataframe,
            subject_id=subject_id,
            image_metadata=image_metadata,
            only_valid_fixations=only_valid_fixations,
        )

        records.extend(file_records)

    return records


def convert_ueyes_to_ndjson(
    root: str | Path,
    output_path: str | Path,
    *,
    only_valid_fixations: bool = True,
    max_files: int | None = None,
) -> None:
    records = load_ueyes(
        root=root,
        only_valid_fixations=only_valid_fixations,
        max_files=max_files,
    )

    write_scanpath_ndjson(records, output_path)


def load_ueyes_image_types(path: str | Path) -> dict[str, dict[str, Any]]:
    dataframe = pd.read_csv(path, sep=";")

    dataframe = dataframe.rename(
        columns={
            "Image Name": "image_id",
            "Category": "category",
            "Block": "block",
            "Train/Test": "split",
        }
    )

    required = {"image_id", "category"}
    missing = required - set(dataframe.columns)

    if missing:
        raise ValueError(
            f"image_types.csv is missing columns: {sorted(missing)}. "
            f"Available columns: {list(dataframe.columns)}"
        )

    metadata: dict[str, dict[str, Any]] = {}

    for _, row in dataframe.iterrows():
        image_id = str(row["image_id"])

        metadata[image_id] = {
            "category": str(row["category"]),
        }

        if "block" in row and pd.notna(row["block"]):
            metadata[image_id]["block"] = str(row["block"])

        if "split" in row and pd.notna(row["split"]):
            metadata[image_id]["split"] = str(row["split"]).lower()

    return metadata


def iter_ueyes_fixation_files(logs_dir: Path) -> list[Path]:
    files: list[Path] = []

    for path in sorted(logs_dir.glob("*_fixations.csv")):
        name = path.name

        if name.startswith("."):
            continue

        if name.startswith("._"):
            continue

        if name.startswith(".~lock"):
            continue

        if "__MACOSX" in path.parts:
            continue

        if not path.is_file():
            continue

        files.append(path)

    return files


def parse_subject_id_from_filename(filename: str) -> str:
    """
    Parse filenames such as:

        00_KH005_fixations.csv
        18_kh008_fixations.csv

    Returns:
        kh005
        kh008
    """
    match = re.match(
        r"\d+_(?P<subject_id>[A-Za-z]+\d+)_fixations\.csv$",
        filename,
    )

    if match is None:
        raise ValueError(f"Unexpected UEyes fixation filename: {filename}")

    return match.group("subject_id").lower()


def ueyes_fixation_dataframe_to_records(
    dataframe: pd.DataFrame,
    *,
    subject_id: str,
    image_metadata: dict[str, dict[str, Any]],
    only_valid_fixations: bool,
) -> list[ScanpathRecord]:
    required_columns = {
        "MEDIA_NAME",
        "FPOGX",
        "FPOGY",
        "FPOGS",
        "FPOGD",
        "FPOGID",
        "FPOGV",
    }

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError(
            f"UEyes fixation file is missing columns: {sorted(missing)}. "
            f"Available columns: {list(dataframe.columns)}"
        )

    if only_valid_fixations:
        dataframe = dataframe[dataframe["FPOGV"] == 1].copy()

    if dataframe.empty:
        return []

    records: list[ScanpathRecord] = []

    for image_id, group in dataframe.groupby("MEDIA_NAME"):
        image_id = str(image_id)

        metadata = image_metadata.get(image_id, {})

        group = group.sort_values(["FPOGS", "FPOGID"]).reset_index(drop=True)

        fixations: list[Fixation] = []

        for fixation_index, (_, row) in enumerate(group.iterrows()):
            fixations.append(
                Fixation(
                    fixation_index=fixation_index,
                    timestamp=float(row["FPOGS"]) * 1000.0,
                    x=float(row["FPOGX"]),
                    y=float(row["FPOGY"]),
                    duration=float(row["FPOGD"]) * 1000.0,
                )
            )

        record_metadata: dict[str, Any] = {}

        if "category" in metadata:
            record_metadata["category"] = metadata["category"]

        if "block" in metadata:
            record_metadata["block"] = metadata["block"]

        split = metadata.get("split")

        records.append(
            ScanpathRecord(
                schema_version=UEYES_SCHEMA_VERSION,
                source="human",
                dataset="ueyes",
                image_id=image_id,
                trial_id=f"{subject_id}_{image_id}",
                subject_id=subject_id,
                split=split,
                stimulus={
                    "path": image_id,
                },
                coordinate_system=DEFAULT_COORDINATE_SYSTEM,
                time_unit="ms",
                duration_unit="ms",
                scanpath=fixations,
                metadata=record_metadata,
            )
        )

    return records
