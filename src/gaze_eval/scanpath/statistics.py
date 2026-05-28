from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd


COMPARISON_ORDER = [
    "same_image",
    "same_category",
    "different_category",
]

PAIRWISE_COMPARISONS = [
    ("same_image", "same_category"),
    ("same_category", "different_category"),
    ("same_image", "different_category"),
]


@dataclass(frozen=True)
class BootstrapConfig:
    n_bootstrap: int = 5000
    confidence_level: float = 0.95
    random_state: int = 42


def summarize_metric_distributions(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """
    Summarize metric values by metric and comparison type.

    Expected input columns:
        metric, direction, comparison_type, value

    Returns one row per:
        metric × direction × comparison_type
    """
    required = {"metric", "direction", "comparison_type", "value"}
    validate_columns(results, required)

    return (
        results.dropna(subset=["value"])
        .groupby(["metric", "direction", "comparison_type"], as_index=False)
        .agg(
            mean=("value", "mean"),
            median=("value", "median"),
            std=("value", "std"),
            q25=("value", lambda values: values.quantile(0.25)),
            q75=("value", lambda values: values.quantile(0.75)),
            count=("value", "count"),
        )
        .sort_values(["metric", "comparison_type"])
        .reset_index(drop=True)
    )


def analyze_metric_group_differences(
    results: pd.DataFrame,
    *,
    bootstrap: BootstrapConfig | None = None,
) -> pd.DataFrame:
    """
    Compute pairwise group differences for each metric.

    For lower-is-better metrics:
        positive oriented differences mean group A is better than group B.

        oriented_median_difference = median(B) - median(A)

    For higher-is-better metrics:
        positive oriented differences mean group A is better than group B.

        oriented_median_difference = median(A) - median(B)

    Effect size:
        Uses oriented Cliff's delta.

        +1 means all values in group A are better than group B.
         0 means no ordering tendency.
        -1 means group A is worse than group B.
    """
    required = {"metric", "direction", "comparison_type", "value"}
    validate_columns(results, required)

    if bootstrap is None:
        bootstrap = BootstrapConfig()

    rows: list[dict[str, object]] = []

    clean = results.dropna(subset=["value"]).copy()

    for (metric, direction), metric_df in clean.groupby(["metric", "direction"]):
        if direction not in {"lower", "higher"}:
            continue

        for group_a, group_b in PAIRWISE_COMPARISONS:
            values_a = metric_df.loc[
                metric_df["comparison_type"] == group_a,
                "value",
            ].to_numpy(dtype=float)

            values_b = metric_df.loc[
                metric_df["comparison_type"] == group_b,
                "value",
            ].to_numpy(dtype=float)

            if len(values_a) == 0 or len(values_b) == 0:
                continue

            median_a = float(np.median(values_a))
            median_b = float(np.median(values_b))

            mean_a = float(np.mean(values_a))
            mean_b = float(np.mean(values_b))

            oriented_median_difference = oriented_difference(
                median_a,
                median_b,
                direction=direction,
            )

            oriented_mean_difference = oriented_difference(
                mean_a,
                mean_b,
                direction=direction,
            )

            ci_low, ci_high = bootstrap_oriented_difference_ci(
                values_a,
                values_b,
                direction=direction,
                statistic=np.median,
                config=bootstrap,
            )

            delta = cliffs_delta(values_a, values_b)
            oriented_delta = orient_effect_size(delta, direction=direction)

            probability_a_better = probability_first_group_better(
                values_a,
                values_b,
                direction=direction,
            )

            rows.append(
                {
                    "metric": metric,
                    "direction": direction,
                    "group_a": group_a,
                    "group_b": group_b,
                    "n_a": len(values_a),
                    "n_b": len(values_b),
                    "median_a": median_a,
                    "median_b": median_b,
                    "mean_a": mean_a,
                    "mean_b": mean_b,
                    "oriented_median_difference": oriented_median_difference,
                    "oriented_mean_difference": oriented_mean_difference,
                    "bootstrap_ci_low": ci_low,
                    "bootstrap_ci_high": ci_high,
                    "oriented_cliffs_delta": oriented_delta,
                    "probability_a_better": probability_a_better,
                    "passes_expected_direction": oriented_median_difference > 0,
                    "ci_excludes_zero": ci_low > 0 or ci_high < 0,
                }
            )

    return pd.DataFrame(rows)


def check_expected_similarity_order(
    summary: pd.DataFrame,
) -> pd.DataFrame:
    """
    Check whether metric medians follow the expected order.

    For lower-is-better metrics:
        same_image < same_category < different_category

    For higher-is-better metrics:
        same_image > same_category > different_category
    """
    required = {"metric", "direction", "comparison_type", "median"}
    validate_columns(summary, required)

    rows: list[dict[str, object]] = []

    for (metric, direction), group in summary.groupby(["metric", "direction"]):
        if direction not in {"lower", "higher"}:
            continue

        values = {row["comparison_type"]: row["median"] for _, row in group.iterrows()}

        if not set(COMPARISON_ORDER).issubset(values):
            continue

        same_image = values["same_image"]
        same_category = values["same_category"]
        different_category = values["different_category"]

        if direction == "lower":
            passes = same_image <= same_category <= different_category
        else:
            passes = same_image >= same_category >= different_category

        rows.append(
            {
                "metric": metric,
                "direction": direction,
                "same_image_median": same_image,
                "same_category_median": same_category,
                "different_category_median": different_category,
                "passes_expected_order": passes,
            }
        )

    return pd.DataFrame(rows)


def compute_human_baseline_quality_scores(
    summary: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute a normalized metric-quality scale from human-human baselines.

    For each metric:

        score = 1.0 means same-image human-human level
        score = 0.0 means different-category human-human level

    This is useful later for model prediction:

        model_score close to 1 = human-like
        model_score close to 0 = weak / different-category-like

    This function only builds the baseline reference from human-human results.
    """
    required = {"metric", "direction", "comparison_type", "median"}
    validate_columns(summary, required)

    rows: list[dict[str, object]] = []

    for (metric, direction), group in summary.groupby(["metric", "direction"]):
        if direction not in {"lower", "higher"}:
            continue

        values = {row["comparison_type"]: row["median"] for _, row in group.iterrows()}

        if not {"same_image", "different_category"}.issubset(values):
            continue

        same_image = float(values["same_image"])
        different_category = float(values["different_category"])

        denominator = abs(different_category - same_image)

        rows.append(
            {
                "metric": metric,
                "direction": direction,
                "human_like_reference": same_image,
                "weak_reference": different_category,
                "reference_range": denominator,
                "interpretation": (
                    "For future model evaluation, values closer to "
                    "human_like_reference are better."
                ),
            }
        )

    return pd.DataFrame(rows)


def score_model_against_human_baseline(
    model_results: pd.DataFrame,
    baseline: pd.DataFrame,
) -> pd.DataFrame:
    """
    Score model-vs-human metric values against human-human baselines.

    The score is normalized so that:

        1.0 = same-image human-human level
        0.0 = different-category human-human level

    Scores may be below 0 or above 1 if the model is outside the human baseline range.
    """
    required_model = {"metric", "direction", "value"}
    required_baseline = {
        "metric",
        "direction",
        "human_like_reference",
        "weak_reference",
        "reference_range",
    }

    validate_columns(model_results, required_model)
    validate_columns(baseline, required_baseline)

    model_summary = (
        model_results.dropna(subset=["value"])
        .groupby(["metric", "direction"], as_index=False)
        .agg(
            model_median=("value", "median"),
            model_mean=("value", "mean"),
            model_count=("value", "count"),
        )
    )

    scored = model_summary.merge(
        baseline,
        on=["metric", "direction"],
        how="inner",
    )

    scores = []

    for _, row in scored.iterrows():
        score = normalized_quality_score(
            value=float(row["model_median"]),
            human_like_reference=float(row["human_like_reference"]),
            weak_reference=float(row["weak_reference"]),
            direction=str(row["direction"]),
        )
        scores.append(score)

    scored["human_normalized_score"] = scores

    return scored


def normalized_quality_score(
    value: float,
    *,
    human_like_reference: float,
    weak_reference: float,
    direction: str,
) -> float:
    denominator = abs(weak_reference - human_like_reference)

    if np.isclose(denominator, 0.0):
        return np.nan

    if direction == "lower":
        return (weak_reference - value) / denominator

    if direction == "higher":
        return (value - weak_reference) / denominator

    return np.nan


def oriented_difference(
    value_a: float,
    value_b: float,
    *,
    direction: str,
) -> float:
    """
    Return positive values when A is better than B.
    """
    if direction == "lower":
        return value_b - value_a

    if direction == "higher":
        return value_a - value_b

    raise ValueError(f"Unsupported metric direction: {direction}")


def bootstrap_oriented_difference_ci(
    values_a: np.ndarray,
    values_b: np.ndarray,
    *,
    direction: str,
    statistic: Callable[[np.ndarray], float],
    config: BootstrapConfig,
) -> tuple[float, float]:
    rng = np.random.default_rng(config.random_state)

    differences = np.empty(config.n_bootstrap, dtype=float)

    for index in range(config.n_bootstrap):
        sample_a = rng.choice(values_a, size=len(values_a), replace=True)
        sample_b = rng.choice(values_b, size=len(values_b), replace=True)

        stat_a = float(statistic(sample_a))
        stat_b = float(statistic(sample_b))

        differences[index] = oriented_difference(
            stat_a,
            stat_b,
            direction=direction,
        )

    alpha = 1.0 - config.confidence_level

    lower = float(np.quantile(differences, alpha / 2.0))
    upper = float(np.quantile(differences, 1.0 - alpha / 2.0))

    return lower, upper


def cliffs_delta(values_a: np.ndarray, values_b: np.ndarray) -> float:
    """
    Compute Cliff's delta.

    Raw interpretation:
        +1 means values in A are always larger than values in B.
         0 means no ordering tendency.
        -1 means values in A are always smaller than values in B.

    For lower-is-better metrics, this is later multiplied by -1.
    """
    values_a = np.asarray(values_a, dtype=float)
    values_b = np.asarray(values_b, dtype=float)

    n_a = len(values_a)
    n_b = len(values_b)

    if n_a == 0 or n_b == 0:
        return np.nan

    greater = 0
    less = 0

    # Chunked implementation to avoid creating very large pairwise matrices.
    chunk_size = 1000

    for start in range(0, n_a, chunk_size):
        chunk = values_a[start : start + chunk_size]
        comparison = chunk[:, None] - values_b[None, :]

        greater += int(np.sum(comparison > 0))
        less += int(np.sum(comparison < 0))

    return (greater - less) / float(n_a * n_b)


def orient_effect_size(
    delta: float,
    *,
    direction: str,
) -> float:
    """
    Return positive effect size when group A is better than group B.
    """
    if direction == "lower":
        return -delta

    if direction == "higher":
        return delta

    return np.nan


def probability_first_group_better(
    values_a: np.ndarray,
    values_b: np.ndarray,
    *,
    direction: str,
) -> float:
    """
    Estimate P(A is better than B) from pairwise comparisons.
    """
    values_a = np.asarray(values_a, dtype=float)
    values_b = np.asarray(values_b, dtype=float)

    if len(values_a) == 0 or len(values_b) == 0:
        return np.nan

    better = 0
    total = 0

    chunk_size = 1000

    for start in range(0, len(values_a), chunk_size):
        chunk = values_a[start : start + chunk_size]

        if direction == "lower":
            comparison = chunk[:, None] < values_b[None, :]
        elif direction == "higher":
            comparison = chunk[:, None] > values_b[None, :]
        else:
            return np.nan

        better += int(np.sum(comparison))
        total += comparison.size

    return better / float(total)


def validate_columns(
    dataframe: pd.DataFrame,
    required_columns: set[str],
) -> None:
    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError(f"dataframe is missing required columns: {sorted(missing)}")
