from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results" / "metrics" / "debug"


LOWER_IS_BETTER = {
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
}

HIGHER_IS_BETTER = {
    "duration_correlation",
    "multimatch_shape",
    "multimatch_direction",
    "multimatch_length",
    "multimatch_position",
    "multimatch_duration",
    "scanmatch",
    "needleman_wunsch",
    "aoi_transition_similarity",
    "sequence_score",
    "mannan_distance",
}

DESCRIPTIVE = {
    "number_of_fixations",
    "aoi_transition_count",
    "recurrence",
    "determinism",
    "laminarity",
    "corm",
}


def load_summary(case_name: str) -> pd.DataFrame:
    path = RESULTS_DIR / f"{case_name}_scanpath_metrics_summary.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run examples/run_dummy_scanpath_eval.py first."
        )

    df = pd.read_csv(path)
    df["case"] = case_name
    return df


def classify_metric(metric: str, same: float, good: float, bad: float) -> str:
    if pd.isna(same) or pd.isna(good) or pd.isna(bad):
        return "undefined_for_at_least_one_case"

    if metric in LOWER_IS_BETTER:
        if same <= good <= bad:
            return "expected_order"
        if good < bad:
            return "partially_expected_good_better_than_bad"
        return "unexpected_order"

    if metric in HIGHER_IS_BETTER:
        if same >= good >= bad:
            return "expected_order"
        if good > bad:
            return "partially_expected_good_better_than_bad"
        return "unexpected_order"

    if metric in DESCRIPTIVE:
        return "descriptive_no_strict_order"

    return "unknown_direction"


def main() -> None:
    same = load_summary("same")
    good = load_summary("good")
    bad = load_summary("bad")

    all_summaries = pd.concat([same, good, bad], ignore_index=True)

    compact = all_summaries.pivot_table(
        index=["metric", "category", "direction"],
        columns="case",
        values="mean",
        aggfunc="first",
    ).reset_index()

    # Make the column order stable.
    compact = compact[["metric", "category", "direction", "same", "good", "bad"]]

    compact["conclusion"] = compact.apply(
        lambda row: classify_metric(
            metric=row["metric"],
            same=row["same"],
            good=row["good"],
            bad=row["bad"],
        ),
        axis=1,
    )

    output_path = RESULTS_DIR / "dummy_metric_comparison_summary.csv"
    compact.to_csv(output_path, index=False)

    print("\nDummy metric comparison summary")
    print("=" * 80)
    print(compact.to_string(index=False))

    print("\nConclusion counts")
    print("=" * 80)
    print(compact["conclusion"].value_counts().to_string())

    print("\nShort interpretation")
    print("=" * 80)

    expected = compact[compact["conclusion"] == "expected_order"]
    partial = compact[
        compact["conclusion"] == "partially_expected_good_better_than_bad"
    ]
    unexpected = compact[compact["conclusion"] == "unexpected_order"]
    descriptive = compact[compact["conclusion"] == "descriptive_no_strict_order"]

    print(
        f"- {len(expected)} metrics follow the full expected order "
        f"between same, good, and bad."
    )
    print(
        f"- {len(partial)} metrics do not perfectly rank same vs good, "
        f"but still separate good from bad."
    )
    print(
        f"- {len(descriptive)} metrics are descriptive and should not be "
        f"interpreted with a strict better/worse order."
    )
    print(
        f"- {len(unexpected)} metrics show an unexpected order and should be checked."
    )

    if len(partial) > 0:
        print("\nPartially expected metrics:")
        print(", ".join(partial["metric"].tolist()))

    if len(unexpected) > 0:
        print("\nUnexpected metrics:")
        print(", ".join(unexpected["metric"].tolist()))

    print(f"\nSaved comparison summary to: {output_path}")


if __name__ == "__main__":
    main()
