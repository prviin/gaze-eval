from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import pandas as pd
from PIL import Image
from tqdm.auto import tqdm

from gaze_eval.scanpath.io import write_scanpath_ndjson
from gaze_eval.scanpath.records import Fixation, ScanpathRecord


MassVisPhase = Literal["enc", "rec", "both"]
OutOfBoundsMode = Literal["keep", "drop", "clip"]

MASSVIS_SCHEMA_VERSION = "gaze-eval-scanpath-v1"

DEFAULT_COORDINATE_SYSTEM = {
    "type": "normalized",
    "x_range": [0, 1],
    "y_range": [0, 1],
    "origin": "top_left",
}


def load_massvis(
    root: str | Path,
    *,
    phase: MassVisPhase = "enc",
    normalize_coordinates: bool = True,
    out_of_bounds: OutOfBoundsMode = "drop",
    drop_missing_stimuli: bool = True,
    show_progress: bool = True,
    max_files: int | None = None,
) -> list[ScanpathRecord]:
    """
    Load MassVis fixation files into gaze-eval ScanpathRecord objects.

    Expected structure:

        root/
        ├── massvis_cat_metadata.csv
        ├── stimuli/
        └── fixationsByVis/
            └── <image_id>/
                ├── enc/
                │   └── <subject_id>.csv
                └── rec/
                    └── <subject_id>.csv

    Each fixation CSV has no header and contains:

        fixation_index, x, y, duration

    The x/y coordinates are pixel coordinates and are normalized by default.
    Duration is assumed to be in milliseconds.
    """
    root = Path(root)
    validate_out_of_bounds_mode(out_of_bounds)

    image_metadata = load_massvis_metadata(root)
    stimulus_paths = index_massvis_stimuli(root)

    fixation_files = iter_massvis_fixation_files(root, phase=phase)

    if max_files is not None:
        fixation_files = fixation_files[:max_files]

    iterator = fixation_files

    if show_progress:
        iterator = tqdm(
            fixation_files,
            desc=f"Loading MassVis fixation files ({phase})",
            unit="file",
        )

    records: list[ScanpathRecord] = []

    for image_id, subject_id, selected_phase, fixation_file in iterator:
        metadata = image_metadata.get(image_id, {})
        stimulus_path = stimulus_paths.get(image_id)
        if normalize_coordinates and drop_missing_stimuli and stimulus_path is None:
            continue

        width_px: int | None = None
        height_px: int | None = None

        if stimulus_path is not None:
            width_px, height_px = read_image_size(stimulus_path)

        dataframe = read_massvis_fixation_file(fixation_file)

        if dataframe.empty:
            continue

        record = massvis_dataframe_to_record(
            dataframe,
            image_id=image_id,
            subject_id=subject_id,
            phase=selected_phase,
            metadata=metadata,
            stimulus_path=stimulus_path,
            width_px=width_px,
            height_px=height_px,
            normalize_coordinates=normalize_coordinates,
            out_of_bounds=out_of_bounds,
        )

        if len(record.scanpath) > 0:
            records.append(record)

    return records


def convert_massvis_to_ndjson(
    root: str | Path,
    output_path: str | Path,
    *,
    phase: MassVisPhase = "enc",
    normalize_coordinates: bool = True,
    out_of_bounds: OutOfBoundsMode = "drop",
    drop_missing_stimuli: bool = True,
    show_progress: bool = True,
    max_files: int | None = None,
) -> None:
    records = load_massvis(
        root=root,
        phase=phase,
        normalize_coordinates=normalize_coordinates,
        out_of_bounds=out_of_bounds,
        drop_missing_stimuli=drop_missing_stimuli,
        show_progress=show_progress,
        max_files=max_files,
    )

    write_scanpath_ndjson(records, output_path)


def resolve_massvis_phases(phase: MassVisPhase) -> list[str]:
    if phase == "both":
        return ["enc", "rec"]

    if phase in {"enc", "rec"}:
        return [phase]

    raise ValueError(
        f"Unsupported MassVis phase: {phase}. Expected one of: 'enc', 'rec', 'both'."
    )


def iter_massvis_fixation_files(
    root: str | Path,
    *,
    phase: MassVisPhase = "enc",
) -> list[tuple[str, str, str, Path]]:
    """
    Return MassVis fixation files.

    Returns
    -------
    list[tuple[str, str, str, Path]]
        Tuples of:

            image_id, subject_id, phase, fixation_file
    """
    root = Path(root)
    fixations_root = root / "fixationsByVis"

    if not fixations_root.exists():
        raise FileNotFoundError(f"Could not find {fixations_root}")

    phases = resolve_massvis_phases(phase)

    files: list[tuple[str, str, str, Path]] = []

    for image_dir in sorted(fixations_root.iterdir()):
        if not image_dir.is_dir():
            continue

        image_id = image_dir.name

        for selected_phase in phases:
            phase_dir = image_dir / selected_phase

            if not phase_dir.exists():
                continue

            for fixation_file in sorted(phase_dir.glob("*.csv")):
                if fixation_file.name.startswith("."):
                    continue

                subject_id = fixation_file.stem

                files.append(
                    (
                        image_id,
                        subject_id,
                        selected_phase,
                        fixation_file,
                    )
                )

    return files


def read_massvis_fixation_file(path: str | Path) -> pd.DataFrame:
    dataframe = pd.read_csv(
        path,
        header=None,
        names=["fixation_index", "x", "y", "duration"],
    )

    dataframe = dataframe.dropna(subset=["x", "y", "duration"]).copy()

    dataframe["fixation_index"] = dataframe["fixation_index"].astype(int)
    dataframe["x"] = dataframe["x"].astype(float)
    dataframe["y"] = dataframe["y"].astype(float)
    dataframe["duration"] = dataframe["duration"].astype(float)

    return dataframe


def load_massvis_metadata(root: str | Path) -> dict[str, dict[str, Any]]:
    root = Path(root)
    metadata_path = root / "massvis_cat_metadata.csv"

    if not metadata_path.exists():
        return {}

    dataframe = pd.read_csv(metadata_path, encoding="latin1")
    dataframe = standardize_massvis_metadata_columns(dataframe)

    metadata: dict[str, dict[str, Any]] = {}

    for _, row in dataframe.iterrows():
        image_id = str(row["image_id"])

        item: dict[str, Any] = {}

        if "category" in row and pd.notna(row["category"]):
            item["category"] = normalize_massvis_category(row["category"])

        if "vistype" in row and pd.notna(row["vistype"]):
            item["vistype"] = str(row["vistype"])

        if "source" in row and pd.notna(row["source"]):
            item["stimulus_source"] = str(row["source"])

        if "title" in row and pd.notna(row["title"]):
            item["title"] = str(row["title"])

        if "title_location" in row and pd.notna(row["title_location"]):
            item["title_location"] = str(row["title_location"])

        metadata[image_id] = item

    return metadata


def standardize_massvis_metadata_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    column_mapping = {
        "filename": "image_id",
        "image_id": "image_id",
        "image": "image_id",
        "vis": "image_id",
        "vis_id": "image_id",
        "name": "image_id",
        "file": "image_id",
        "category": "category",
        "cat": "category",
        "vistype": "vistype",
        "vis type": "vistype",
        "type": "vistype",
        "source": "source",
        "title": "title",
        "title location": "title_location",
    }

    dataframe = dataframe.rename(
        columns={
            column: column_mapping[column.lower().strip()]
            for column in dataframe.columns
            if column.lower().strip() in column_mapping
        }
    )

    if "image_id" not in dataframe.columns:
        first_column = dataframe.columns[0]
        dataframe = dataframe.rename(columns={first_column: "image_id"})

    dataframe["image_id"] = dataframe["image_id"].map(
        lambda value: Path(str(value)).stem
    )

    return dataframe


def normalize_massvis_category(value: object) -> str:
    category = str(value).strip().upper()

    category_mapping = {
        "N": "news",
        "S": "science",
        "G": "government",
        "I": "infographic",
    }

    return category_mapping.get(category, str(value).strip().lower())


def index_massvis_stimuli(root: str | Path) -> dict[str, Path]:
    root = Path(root)
    stimuli_root = root / "stimuli"

    if not stimuli_root.exists():
        return {}

    paths: dict[str, Path] = {}

    for path in stimuli_root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue

        image_id = path.stem
        paths[image_id] = path

    return paths


def read_image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def validate_out_of_bounds_mode(out_of_bounds: OutOfBoundsMode) -> None:
    if out_of_bounds not in {"keep", "drop", "clip"}:
        raise ValueError(
            f"Unsupported out_of_bounds mode: {out_of_bounds}. "
            "Expected one of: 'keep', 'drop', 'clip'."
        )


def massvis_dataframe_to_record(
    dataframe: pd.DataFrame,
    *,
    image_id: str,
    subject_id: str,
    phase: str,
    metadata: dict[str, Any],
    stimulus_path: Path | None,
    width_px: int | None,
    height_px: int | None,
    normalize_coordinates: bool,
    out_of_bounds: OutOfBoundsMode,
) -> ScanpathRecord:
    dataframe = dataframe.sort_values("fixation_index").reset_index(drop=True)

    fixations: list[Fixation] = []

    for new_index, row in dataframe.iterrows():
        x = float(row["x"])
        y = float(row["y"])

        has_image_size = width_px is not None and height_px is not None

        if normalize_coordinates and has_image_size:
            assert width_px is not None
            assert height_px is not None

            is_out_of_bounds = (
                x < 0.0 or x > float(width_px) or y < 0.0 or y > float(height_px)
            )

            if is_out_of_bounds and out_of_bounds == "drop":
                continue

            if is_out_of_bounds and out_of_bounds == "clip":
                x = min(max(x, 0.0), float(width_px))
                y = min(max(y, 0.0), float(height_px))

            x = x / float(width_px)
            y = y / float(height_px)

        fixations.append(
            Fixation(
                fixation_index=len(fixations),
                timestamp=None,
                x=x,
                y=y,
                duration=float(row["duration"]),
            )
        )

    record_metadata: dict[str, Any] = {
        "phase": phase,
    }

    if "category" in metadata:
        record_metadata["category"] = metadata["category"]

    if "vistype" in metadata:
        record_metadata["vistype"] = metadata["vistype"]

    if "stimulus_source" in metadata:
        record_metadata["stimulus_source"] = metadata["stimulus_source"]

    if "title" in metadata:
        record_metadata["title"] = metadata["title"]

    if "title_location" in metadata:
        record_metadata["title_location"] = metadata["title_location"]

    stimulus: dict[str, Any] = {}

    if stimulus_path is not None:
        stimulus["path"] = str(stimulus_path)

    if width_px is not None:
        stimulus["width_px"] = width_px

    if height_px is not None:
        stimulus["height_px"] = height_px

    if normalize_coordinates and width_px is not None and height_px is not None:
        coordinate_system = DEFAULT_COORDINATE_SYSTEM
    else:
        coordinate_system = {
            "type": "pixel",
            "origin": "top_left",
        }
    return ScanpathRecord(
        schema_version=MASSVIS_SCHEMA_VERSION,
        source="human",
        dataset="massvis",
        image_id=image_id,
        trial_id=f"{subject_id}_{image_id}_{phase}",
        subject_id=subject_id,
        stimulus=stimulus,
        coordinate_system=coordinate_system,
        time_unit="ms",
        duration_unit="ms",
        scanpath=fixations,
        metadata=record_metadata,
    )
