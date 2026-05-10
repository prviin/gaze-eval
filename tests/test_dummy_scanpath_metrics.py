from pathlib import Path

import pandas as pd

from gaze_eval.scanpath.metrics import (
    dtw_distance,
    final_fixation_error,
    mean_duration_error,
    mean_fixation_error,
    sequence_score,
)


DATA_DIR = Path(__file__).parent / "data" / "debug"


def _load_human_subject(subject_id: str) -> pd.DataFrame:
    human = pd.read_csv(DATA_DIR / "human_scanpaths.csv")
    return human[human["subject_id"] == subject_id]


def _load_pred(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / f"pred_{name}.csv")


def test_mean_fixation_error_order() -> None:
    human = _load_human_subject("s01")

    same = mean_fixation_error(_load_pred("same"), human)
    good = mean_fixation_error(_load_pred("good"), human)
    bad = mean_fixation_error(_load_pred("bad"), human)

    assert same == 0.0
    assert same < good < bad


def test_final_fixation_error_order() -> None:
    human = _load_human_subject("s01")

    same = final_fixation_error(_load_pred("same"), human)
    good = final_fixation_error(_load_pred("good"), human)
    bad = final_fixation_error(_load_pred("bad"), human)

    assert same == 0.0
    assert same <= good < bad


def test_mean_duration_error_order() -> None:
    human = _load_human_subject("s01")

    same = mean_duration_error(_load_pred("same"), human)
    good = mean_duration_error(_load_pred("good"), human)
    bad = mean_duration_error(_load_pred("bad"), human)

    assert same == 0.0
    assert same < good < bad


def test_dtw_order() -> None:
    human = _load_human_subject("s01")

    same = dtw_distance(_load_pred("same"), human)
    good = dtw_distance(_load_pred("good"), human)
    bad = dtw_distance(_load_pred("bad"), human)

    assert same == 0.0
    assert same < good < bad


def test_sequence_score_order() -> None:
    human = _load_human_subject("s01")

    same = sequence_score(_load_pred("same"), human)
    good = sequence_score(_load_pred("good"), human)
    bad = sequence_score(_load_pred("bad"), human)

    assert same == 1.0
    assert same >= good >= bad
