from pathlib import Path

import pandas as pd

from gaze_eval.scanpath.aggregate import aggregate_scanpath_results
from gaze_eval.scanpath.evaluate import evaluate_scanpaths


DATA_DIR = Path(__file__).parent / "data" / "debug"


LOWER_IS_BETTER_METRICS = [
    "mean_fixation_error",
    "final_fixation_error",
    "mean_saccade_amplitude_error",
    "mean_saccade_angle_error",
    "mean_duration_error",
    "dtw",
    "frechet",
    "hausdorff",
    "levenshtein",
    "eyenalysis",
    "tde",
    "scaled_tde",
]

HIGHER_IS_BETTER_METRICS = [
    "scanmatch",
    "needleman_wunsch",
    "aoi_transition_similarity",
    "sequence_score",
    "mannan_distance",
]

# MultiMatch needs the optional dependency `multimatch-gaze`.
# Keep it out of this core test unless you install that dependency in CI.
OPTIONAL_MULTIMATCH_METRICS = [
    "multimatch_shape",
    "multimatch_direction",
    "multimatch_length",
    "multimatch_position",
    "multimatch_duration",
]

DESCRIPTIVE_METRICS = [
    "number_of_fixations",
    "aoi_transition_count",
    "recurrence",
    "determinism",
    "laminarity",
    "corm",
]


def _evaluate_case(case_name: str, metric_names: list[str]) -> pd.DataFrame:
    human = pd.read_csv(DATA_DIR / "human_scanpaths.csv")
    pred = pd.read_csv(DATA_DIR / f"pred_{case_name}.csv")

    raw = evaluate_scanpaths(
        human_scanpaths=human,
        predicted_scanpaths=pred,
        metric_names=metric_names,
    )

    return aggregate_scanpath_results(raw)


def _metric_mean(summary: pd.DataFrame, metric_name: str) -> float:
    row = summary[summary["metric"] == metric_name]

    assert len(row) == 1, f"Expected one summary row for {metric_name}"

    return float(row["mean"].iloc[0])


def test_lower_is_better_metrics_ordering() -> None:
    same = _evaluate_case("same", LOWER_IS_BETTER_METRICS)
    good = _evaluate_case("good", LOWER_IS_BETTER_METRICS)
    bad = _evaluate_case("bad", LOWER_IS_BETTER_METRICS)

    for metric_name in LOWER_IS_BETTER_METRICS:
        same_value = _metric_mean(same, metric_name)
        good_value = _metric_mean(good, metric_name)
        bad_value = _metric_mean(bad, metric_name)

        assert same_value <= good_value <= bad_value, (
            f"{metric_name} failed expected ordering: "
            f"same={same_value}, good={good_value}, bad={bad_value}"
        )


def test_higher_is_better_metrics_ordering() -> None:
    same = _evaluate_case("same", HIGHER_IS_BETTER_METRICS)
    good = _evaluate_case("good", HIGHER_IS_BETTER_METRICS)
    bad = _evaluate_case("bad", HIGHER_IS_BETTER_METRICS)

    for metric_name in HIGHER_IS_BETTER_METRICS:
        same_value = _metric_mean(same, metric_name)
        good_value = _metric_mean(good, metric_name)
        bad_value = _metric_mean(bad, metric_name)

        assert same_value >= good_value >= bad_value, (
            f"{metric_name} failed expected ordering: "
            f"same={same_value}, good={good_value}, bad={bad_value}"
        )


def test_descriptive_metrics_return_values_without_crashing() -> None:
    summary = _evaluate_case("good", DESCRIPTIVE_METRICS)

    assert set(summary["metric"]) == set(DESCRIPTIVE_METRICS)

    # Some recurrence metrics may be NaN depending on the threshold,
    # so here we only check that the rows are produced.
    assert len(summary) == len(DESCRIPTIVE_METRICS)
