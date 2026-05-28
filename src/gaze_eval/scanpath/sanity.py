from __future__ import annotations

import pandas as pd


def summarize_similarity_by_comparison_type(results: pd.DataFrame) -> pd.DataFrame:
    return (
        results.dropna(subset=["value"])
        .groupby(["metric", "direction", "comparison_type"], as_index=False)["value"]
        .agg(["mean", "median", "std", "count"])
        .reset_index()
        .sort_values(["metric", "comparison_type"])
    )


def check_expected_similarity_order(summary: pd.DataFrame) -> pd.DataFrame:
    """
    For lower-is-better metrics:
        same_image < same_category < different_category

    For higher-is-better metrics:
        same_image > same_category > different_category
    """
    rows: list[dict[str, object]] = []

    for (metric, direction), group in summary.groupby(["metric", "direction"]):
        values = {row["comparison_type"]: row["median"] for _, row in group.iterrows()}

        required = {"same_image", "same_category", "different_category"}

        if not required.issubset(values):
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
