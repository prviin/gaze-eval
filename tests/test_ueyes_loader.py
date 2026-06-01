from __future__ import annotations

from pathlib import Path

import pandas as pd

from gaze_eval.datasets.ueyes import load_ueyes


def test_load_ueyes_sample_converts_to_scanpath_records(tmp_path: Path) -> None:
    dataset_root = tmp_path / "UEyes_dataset"
    logs_dir = dataset_root / "eyetracker_logs"
    logs_dir.mkdir(parents=True)

    image_types = pd.DataFrame(
        {
            "Image Name": ["img_001.png", "img_002.png"],
            "Category": ["desktop", "mobile"],
            "Block": ["0", "1"],
            "Train/Test": ["Train", "Test"],
        }
    )
    image_types.to_csv(dataset_root / "image_types.csv", sep=";", index=False)

    fixations = pd.DataFrame(
        {
            "MEDIA_ID": [1, 1, 2, 2],
            "MEDIA_NAME": [
                "img_001.png",
                "img_001.png",
                "img_002.png",
                "img_002.png",
            ],
            "FPOGX": [0.10, 0.20, 0.30, 0.40],
            "FPOGY": [0.15, 0.25, 0.35, 0.45],
            "FPOGS": [0.0, 0.2, 0.0, 0.3],
            "FPOGD": [0.10, 0.15, 0.20, 0.25],
            "FPOGID": [1, 2, 1, 2],
            "FPOGV": [1, 1, 1, 1],
        }
    )
    fixations.to_csv(logs_dir / "00_KH001_fixations.csv", index=False)

    records = load_ueyes(dataset_root)

    assert len(records) == 2

    first = records[0]

    assert first.dataset == "ueyes"
    assert first.source == "human"
    assert first.subject_id == "kh001"
    assert first.image_id in {"img_001.png", "img_002.png"}
    assert len(first.scanpath) == 2

    assert first.scanpath[0].timestamp == 0.0
    assert first.scanpath[0].duration in {100.0, 200.0}

    assert 0.0 <= first.scanpath[0].x <= 1.0
    assert 0.0 <= first.scanpath[0].y <= 1.0

    assert first.metadata["category"] in {"desktop", "mobile"}
    assert first.split in {"train", "test"}


def test_load_ueyes_filters_invalid_fixations(tmp_path: Path) -> None:
    dataset_root = tmp_path / "UEyes_dataset"
    logs_dir = dataset_root / "eyetracker_logs"
    logs_dir.mkdir(parents=True)

    image_types = pd.DataFrame(
        {
            "Image Name": ["img_001.png"],
            "Category": ["desktop"],
            "Block": ["0"],
            "Train/Test": ["Train"],
        }
    )
    image_types.to_csv(dataset_root / "image_types.csv", sep=";", index=False)

    fixations = pd.DataFrame(
        {
            "MEDIA_ID": [1, 1, 1],
            "MEDIA_NAME": ["img_001.png", "img_001.png", "img_001.png"],
            "FPOGX": [0.10, 0.20, 0.30],
            "FPOGY": [0.15, 0.25, 0.35],
            "FPOGS": [0.0, 0.2, 0.4],
            "FPOGD": [0.10, 0.15, 0.20],
            "FPOGID": [1, 2, 3],
            "FPOGV": [1, 0, 1],
        }
    )
    fixations.to_csv(logs_dir / "00_KH001_fixations.csv", index=False)

    records = load_ueyes(dataset_root, only_valid_fixations=True)

    assert len(records) == 1
    assert len(records[0].scanpath) == 2

    timestamps = [fixation.timestamp for fixation in records[0].scanpath]
    durations = [fixation.duration for fixation in records[0].scanpath]

    assert timestamps == [0.0, 400.0]
    assert durations == [100.0, 200.0]


def test_load_ueyes_can_keep_invalid_fixations(tmp_path: Path) -> None:
    dataset_root = tmp_path / "UEyes_dataset"
    logs_dir = dataset_root / "eyetracker_logs"
    logs_dir.mkdir(parents=True)

    image_types = pd.DataFrame(
        {
            "Image Name": ["img_001.png"],
            "Category": ["desktop"],
            "Block": ["0"],
            "Train/Test": ["Train"],
        }
    )
    image_types.to_csv(dataset_root / "image_types.csv", sep=";", index=False)

    fixations = pd.DataFrame(
        {
            "MEDIA_ID": [1, 1, 1],
            "MEDIA_NAME": ["img_001.png", "img_001.png", "img_001.png"],
            "FPOGX": [0.10, 0.20, 0.30],
            "FPOGY": [0.15, 0.25, 0.35],
            "FPOGS": [0.0, 0.2, 0.4],
            "FPOGD": [0.10, 0.15, 0.20],
            "FPOGID": [1, 2, 3],
            "FPOGV": [1, 0, 1],
        }
    )
    fixations.to_csv(logs_dir / "00_KH001_fixations.csv", index=False)

    records = load_ueyes(dataset_root, only_valid_fixations=False)

    assert len(records) == 1
    assert len(records[0].scanpath) == 3
