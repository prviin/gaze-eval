from __future__ import annotations

from pathlib import Path

import pandas as pd
from PIL import Image

from gaze_eval.datasets.massvis import load_massvis


def make_fake_massvis_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "masviss_data"

    stimuli_dir = root / "stimuli" / "news"
    enc_dir = root / "fixationsByVis" / "img_001" / "enc"
    rec_dir = root / "fixationsByVis" / "img_001" / "rec"

    stimuli_dir.mkdir(parents=True)
    enc_dir.mkdir(parents=True)
    rec_dir.mkdir(parents=True)

    # Create a real image so the loader can read width/height.
    image = Image.new("RGB", (100, 200))
    image.save(stimuli_dir / "img_001.png")

    metadata = pd.DataFrame(
        {
            "filename": ["img_001.png"],
            "source": ["Test Source"],
            "category": ["N"],
            "vistype": ["Bars"],
            "title": ["Test visualization"],
            "title location": ["Top-left"],
        }
    )
    metadata.to_csv(root / "massvis_cat_metadata.csv", index=False)

    # CSV has no header:
    # fixation_index, x, y, duration
    enc_fixations = pd.DataFrame(
        [
            [1, 10.0, 20.0, 100.0],
            [2, 50.0, 100.0, 200.0],
            [3, 120.0, 50.0, 150.0],  # out of image bounds, should be dropped
        ]
    )
    enc_fixations.to_csv(enc_dir / "s01.csv", index=False, header=False)

    rec_fixations = pd.DataFrame(
        [
            [1, 20.0, 40.0, 120.0],
            [2, 80.0, 160.0, 180.0],
        ]
    )
    rec_fixations.to_csv(rec_dir / "s01.csv", index=False, header=False)

    return root


def test_load_massvis_enc_normalizes_coordinates_and_drops_out_of_bounds(
    tmp_path: Path,
) -> None:
    root = make_fake_massvis_dataset(tmp_path)

    records = load_massvis(
        root,
        phase="enc",
        normalize_coordinates=True,
        out_of_bounds="drop",
        drop_missing_stimuli=True,
        show_progress=False,
    )

    assert len(records) == 1

    record = records[0]

    assert record.dataset == "massvis"
    assert record.source == "human"
    assert record.image_id == "img_001"
    assert record.subject_id == "s01"
    assert record.trial_id == "s01_img_001_enc"

    assert record.coordinate_system["type"] == "normalized"

    assert record.metadata["phase"] == "enc"
    assert record.metadata["category"] == "news"
    assert record.metadata["vistype"] == "Bars"
    assert record.metadata["stimulus_source"] == "Test Source"
    assert record.metadata["title"] == "Test visualization"
    assert record.metadata["title_location"] == "Top-left"

    # Third fixation was out-of-bounds and should be removed.
    assert len(record.scanpath) == 2

    first = record.scanpath[0]
    second = record.scanpath[1]

    assert first.fixation_index == 0
    assert first.x == 0.1
    assert first.y == 0.1
    assert first.duration == 100.0
    assert first.timestamp is None

    assert second.fixation_index == 1
    assert second.x == 0.5
    assert second.y == 0.5
    assert second.duration == 200.0


def test_load_massvis_rec_phase(tmp_path: Path) -> None:
    root = make_fake_massvis_dataset(tmp_path)

    records = load_massvis(
        root,
        phase="rec",
        normalize_coordinates=True,
        out_of_bounds="drop",
        drop_missing_stimuli=True,
        show_progress=False,
    )

    assert len(records) == 1

    record = records[0]

    assert record.metadata["phase"] == "rec"
    assert record.trial_id == "s01_img_001_rec"
    assert len(record.scanpath) == 2

    assert record.scanpath[0].x == 0.2
    assert record.scanpath[0].y == 0.2
    assert record.scanpath[1].x == 0.8
    assert record.scanpath[1].y == 0.8


def test_load_massvis_both_phases(tmp_path: Path) -> None:
    root = make_fake_massvis_dataset(tmp_path)

    records = load_massvis(
        root,
        phase="both",
        normalize_coordinates=True,
        out_of_bounds="drop",
        drop_missing_stimuli=True,
        show_progress=False,
    )

    assert len(records) == 2

    phases = {record.metadata["phase"] for record in records}
    trial_ids = {record.trial_id for record in records}

    assert phases == {"enc", "rec"}
    assert trial_ids == {
        "s01_img_001_enc",
        "s01_img_001_rec",
    }


def test_load_massvis_clip_out_of_bounds(tmp_path: Path) -> None:
    root = make_fake_massvis_dataset(tmp_path)

    records = load_massvis(
        root,
        phase="enc",
        normalize_coordinates=True,
        out_of_bounds="clip",
        drop_missing_stimuli=True,
        show_progress=False,
    )

    assert len(records) == 1

    record = records[0]

    # The out-of-bounds x=120 for width=100 should be clipped to 1.0.
    assert len(record.scanpath) == 3
    assert record.scanpath[2].x == 1.0
    assert record.scanpath[2].y == 0.25


def test_load_massvis_keep_pixel_when_not_normalizing(tmp_path: Path) -> None:
    root = make_fake_massvis_dataset(tmp_path)

    records = load_massvis(
        root,
        phase="enc",
        normalize_coordinates=False,
        out_of_bounds="keep",
        drop_missing_stimuli=False,
        show_progress=False,
    )

    assert len(records) == 1

    record = records[0]

    assert record.coordinate_system["type"] == "pixel"
    assert len(record.scanpath) == 3

    assert record.scanpath[0].x == 10.0
    assert record.scanpath[0].y == 20.0
    assert record.scanpath[2].x == 120.0
    assert record.scanpath[2].y == 50.0


def test_load_massvis_drops_missing_stimulus_when_requested(tmp_path: Path) -> None:
    root = make_fake_massvis_dataset(tmp_path)

    # Remove the only stimulus image.
    (root / "stimuli" / "news" / "img_001.png").unlink()

    records = load_massvis(
        root,
        phase="enc",
        normalize_coordinates=True,
        out_of_bounds="drop",
        drop_missing_stimuli=True,
        show_progress=False,
    )

    assert records == []


def test_load_massvis_keeps_missing_stimulus_as_pixel_when_allowed(
    tmp_path: Path,
) -> None:
    root = make_fake_massvis_dataset(tmp_path)

    # Remove the only stimulus image.
    (root / "stimuli" / "news" / "img_001.png").unlink()

    records = load_massvis(
        root,
        phase="enc",
        normalize_coordinates=True,
        out_of_bounds="drop",
        drop_missing_stimuli=False,
        show_progress=False,
    )

    assert len(records) == 1
    assert records[0].coordinate_system["type"] == "pixel"
    assert records[0].scanpath[0].x == 10.0
    assert records[0].scanpath[0].y == 20.0
