from __future__ import annotations

import numpy as np
import pandas as pd

from gaze_eval.scanpath.statistics import (
    BootstrapConfig,
    analyze_metric_group_differences,
    check_expected_similarity_order,
    compute_human_baseline_quality_scores,
    normalized_quality_score,
    score_model_against_human_baseline,
    summarize_metric_distributions,
)


def test_summarize_metric_distributions() -> None:
    results = pd.DataFrame(
        {
            "metric": ["dtw", "dtw", "dtw", "dtw"],
            "direction": ["lower", "lower", "lower", "lower"],
            "comparison_type": [
                "same_image",
                "same_image",
                "different_category",
                "different_category",
            ],
            "value": [1.0, 2.0, 3.0, 4.0],
        }
    )

    summary = summarize_metric_distributions(results)

    assert set(summary["comparison_type"]) == {
        "same_image",
        "different_category",
    }

    same_image = summary[summary["comparison_type"] == "same_image"].iloc[0]
    different_category = summary[
        summary["comparison_type"] == "different_category"
    ].iloc[0]

    assert same_image["median"] == 1.5
    assert different_category["median"] == 3.5


def test_check_expected_similarity_order_lower_metric() -> None:
    summary = pd.DataFrame(
        {
            "metric": ["dtw", "dtw", "dtw"],
            "direction": ["lower", "lower", "lower"],
            "comparison_type": [
                "same_image",
                "same_category",
                "different_category",
            ],
            "median": [1.0, 2.0, 3.0],
        }
    )

    sanity = check_expected_similarity_order(summary)

    assert len(sanity) == 1
    assert sanity.iloc[0]["passes_expected_order"] is True or bool(
        sanity.iloc[0]["passes_expected_order"]
    )


def test_check_expected_similarity_order_higher_metric() -> None:
    summary = pd.DataFrame(
        {
            "metric": ["scanmatch", "scanmatch", "scanmatch"],
            "direction": ["higher", "higher", "higher"],
            "comparison_type": [
                "same_image",
                "same_category",
                "different_category",
            ],
            "median": [3.0, 2.0, 1.0],
        }
    )

    sanity = check_expected_similarity_order(summary)

    assert len(sanity) == 1
    assert sanity.iloc[0]["passes_expected_order"] is True or bool(
        sanity.iloc[0]["passes_expected_order"]
    )


def test_check_expected_similarity_order_skips_descriptive_metric() -> None:
    summary = pd.DataFrame(
        {
            "metric": [
                "number_of_fixations",
                "number_of_fixations",
                "number_of_fixations",
            ],
            "direction": ["descriptive", "descriptive", "descriptive"],
            "comparison_type": [
                "same_image",
                "same_category",
                "different_category",
            ],
            "median": [10.0, 10.0, 10.0],
        }
    )

    sanity = check_expected_similarity_order(summary)

    assert sanity.empty


def test_analyze_metric_group_differences_lower_metric() -> None:
    results = pd.DataFrame(
        {
            "metric": ["dtw"] * 9,
            "direction": ["lower"] * 9,
            "comparison_type": (
                ["same_image"] * 3 + ["same_category"] * 3 + ["different_category"] * 3
            ),
            "value": [
                1.0,
                1.1,
                1.2,
                2.0,
                2.1,
                2.2,
                3.0,
                3.1,
                3.2,
            ],
        }
    )

    differences = analyze_metric_group_differences(
        results,
        bootstrap=BootstrapConfig(
            n_bootstrap=100,
            confidence_level=0.95,
            random_state=42,
        ),
    )

    same_vs_different = differences[
        (differences["group_a"] == "same_image")
        & (differences["group_b"] == "different_category")
    ].iloc[0]

    assert same_vs_different["oriented_median_difference"] > 0
    assert same_vs_different["oriented_cliffs_delta"] > 0
    assert same_vs_different["probability_a_better"] == 1.0


def test_analyze_metric_group_differences_higher_metric() -> None:
    results = pd.DataFrame(
        {
            "metric": ["scanmatch"] * 9,
            "direction": ["higher"] * 9,
            "comparison_type": (
                ["same_image"] * 3 + ["same_category"] * 3 + ["different_category"] * 3
            ),
            "value": [
                3.0,
                3.1,
                3.2,
                2.0,
                2.1,
                2.2,
                1.0,
                1.1,
                1.2,
            ],
        }
    )

    differences = analyze_metric_group_differences(
        results,
        bootstrap=BootstrapConfig(
            n_bootstrap=100,
            confidence_level=0.95,
            random_state=42,
        ),
    )

    same_vs_different = differences[
        (differences["group_a"] == "same_image")
        & (differences["group_b"] == "different_category")
    ].iloc[0]

    assert same_vs_different["oriented_median_difference"] > 0
    assert same_vs_different["oriented_cliffs_delta"] > 0
    assert same_vs_different["probability_a_better"] == 1.0


def test_compute_human_baseline_quality_scores() -> None:
    summary = pd.DataFrame(
        {
            "metric": ["dtw", "dtw", "dtw"],
            "direction": ["lower", "lower", "lower"],
            "comparison_type": [
                "same_image",
                "same_category",
                "different_category",
            ],
            "median": [1.0, 2.0, 3.0],
        }
    )

    baseline = compute_human_baseline_quality_scores(summary)

    assert len(baseline) == 1

    row = baseline.iloc[0]

    assert row["human_like_reference"] == 1.0
    assert row["weak_reference"] == 3.0
    assert row["reference_range"] == 2.0


def test_normalized_quality_score_lower_metric() -> None:
    assert (
        normalized_quality_score(
            value=1.0,
            human_like_reference=1.0,
            weak_reference=3.0,
            direction="lower",
        )
        == 1.0
    )

    assert (
        normalized_quality_score(
            value=3.0,
            human_like_reference=1.0,
            weak_reference=3.0,
            direction="lower",
        )
        == 0.0
    )

    assert (
        normalized_quality_score(
            value=2.0,
            human_like_reference=1.0,
            weak_reference=3.0,
            direction="lower",
        )
        == 0.5
    )


def test_normalized_quality_score_higher_metric() -> None:
    assert (
        normalized_quality_score(
            value=3.0,
            human_like_reference=3.0,
            weak_reference=1.0,
            direction="higher",
        )
        == 1.0
    )

    assert (
        normalized_quality_score(
            value=1.0,
            human_like_reference=3.0,
            weak_reference=1.0,
            direction="higher",
        )
        == 0.0
    )

    assert (
        normalized_quality_score(
            value=2.0,
            human_like_reference=3.0,
            weak_reference=1.0,
            direction="higher",
        )
        == 0.5
    )


def test_score_model_against_human_baseline() -> None:
    model_results = pd.DataFrame(
        {
            "metric": ["dtw", "dtw", "dtw"],
            "direction": ["lower", "lower", "lower"],
            "value": [1.5, 2.0, 2.5],
        }
    )

    baseline = pd.DataFrame(
        {
            "metric": ["dtw"],
            "direction": ["lower"],
            "human_like_reference": [1.0],
            "weak_reference": [3.0],
            "reference_range": [2.0],
        }
    )

    scored = score_model_against_human_baseline(
        model_results=model_results,
        baseline=baseline,
    )

    assert len(scored) == 1
    assert np.isclose(scored.iloc[0]["model_median"], 2.0)
    assert np.isclose(scored.iloc[0]["human_normalized_score"], 0.5)
