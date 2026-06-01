from __future__ import annotations

from pathlib import Path

import pandas as pd


PHASE = "enc"

RESULTS_DIR = Path(f"data/processed/massvis/{PHASE}/results")
OUTPUT_DIR = Path(f"data/processed/massvis/{PHASE}/paper_tables")

SUMMARY_PATH = RESULTS_DIR / "massvis_pair_metric_summary_seed42.csv"
SANITY_PATH = RESULTS_DIR / "massvis_pair_metric_sanity_seed42.csv"
DIFFERENCES_PATH = RESULTS_DIR / "massvis_pair_metric_differences_seed42.csv"
BASELINE_PATH = RESULTS_DIR / "massvis_human_baseline_quality_seed42.csv"

PAIRWISE_REFERENCE = ("same_image", "different_category")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary = pd.read_csv(SUMMARY_PATH)
    sanity = pd.read_csv(SANITY_PATH)
    differences = pd.read_csv(DIFFERENCES_PATH)
    baseline = pd.read_csv(BASELINE_PATH)

    main_table = make_main_paper_table(
        summary=summary,
        sanity=sanity,
        differences=differences,
    )

    baseline_table = make_human_baseline_table(baseline)
    appendix_table = make_appendix_summary_table(summary)
    latex_table = dataframe_to_latex_table(main_table)

    main_table_path = OUTPUT_DIR / "massvis_main_metric_table.csv"
    baseline_table_path = OUTPUT_DIR / "massvis_human_baseline_table.csv"
    appendix_table_path = OUTPUT_DIR / "massvis_metric_summary_appendix.csv"
    latex_table_path = OUTPUT_DIR / "massvis_main_metric_table.tex"

    main_table.to_csv(main_table_path, index=False)
    baseline_table.to_csv(baseline_table_path, index=False)
    appendix_table.to_csv(appendix_table_path, index=False)
    latex_table_path.write_text(latex_table, encoding="utf-8")

    print(f"Saved main paper table: {main_table_path}")
    print(f"Saved human baseline table: {baseline_table_path}")
    print(f"Saved appendix summary table: {appendix_table_path}")
    print(f"Saved LaTeX table: {latex_table_path}")

    print("\nMain paper table:")
    print(main_table.to_string(index=False))


def make_main_paper_table(
    *,
    summary: pd.DataFrame,
    sanity: pd.DataFrame,
    differences: pd.DataFrame,
) -> pd.DataFrame:
    medians = pivot_summary_medians(summary)

    reference_differences = extract_reference_differences(
        differences,
        group_a=PAIRWISE_REFERENCE[0],
        group_b=PAIRWISE_REFERENCE[1],
    )

    table = medians.merge(
        sanity[["metric", "passes_expected_order"]],
        on="metric",
        how="left",
    )

    table = table.merge(
        reference_differences,
        on=["metric", "direction"],
        how="left",
    )

    table = table[
        [
            "metric",
            "direction",
            "same_image_median",
            "same_category_median",
            "different_category_median",
            "passes_expected_order",
            "oriented_median_difference",
            "bootstrap_ci",
            "oriented_cliffs_delta",
            "probability_a_better",
            "ci_excludes_zero",
        ]
    ]

    table = table.sort_values(
        by=[
            "passes_expected_order",
            "oriented_cliffs_delta",
            "metric",
        ],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    return round_numeric_columns(table)


def pivot_summary_medians(summary: pd.DataFrame) -> pd.DataFrame:
    usable = summary[summary["direction"].isin(["lower", "higher"])].copy()

    pivot = usable.pivot_table(
        index=["metric", "direction"],
        columns="comparison_type",
        values="median",
        aggfunc="first",
    ).reset_index()

    pivot.columns.name = None

    pivot = pivot.rename(
        columns={
            "same_image": "same_image_median",
            "same_category": "same_category_median",
            "different_category": "different_category_median",
        }
    )

    return pivot[
        [
            "metric",
            "direction",
            "same_image_median",
            "same_category_median",
            "different_category_median",
        ]
    ]


def extract_reference_differences(
    differences: pd.DataFrame,
    *,
    group_a: str,
    group_b: str,
) -> pd.DataFrame:
    reference = differences[
        (differences["group_a"] == group_a) & (differences["group_b"] == group_b)
    ].copy()

    reference["bootstrap_ci"] = reference.apply(
        lambda row: format_ci(
            row["bootstrap_ci_low"],
            row["bootstrap_ci_high"],
        ),
        axis=1,
    )

    return reference[
        [
            "metric",
            "direction",
            "oriented_median_difference",
            "bootstrap_ci",
            "oriented_cliffs_delta",
            "probability_a_better",
            "ci_excludes_zero",
        ]
    ]


def make_human_baseline_table(baseline: pd.DataFrame) -> pd.DataFrame:
    table = baseline[
        [
            "metric",
            "direction",
            "human_like_reference",
            "weak_reference",
            "reference_range",
        ]
    ].copy()

    table = table.rename(
        columns={
            "human_like_reference": "same_image_human_baseline",
            "weak_reference": "different_category_baseline",
            "reference_range": "baseline_range",
        }
    )

    return round_numeric_columns(table)


def make_appendix_summary_table(summary: pd.DataFrame) -> pd.DataFrame:
    table = summary[
        [
            "metric",
            "direction",
            "comparison_type",
            "mean",
            "median",
            "std",
            "q25",
            "q75",
            "count",
        ]
    ].copy()

    return round_numeric_columns(table)


def dataframe_to_latex_table(table: pd.DataFrame) -> str:
    latex_table = table.copy()

    latex_table = latex_table.rename(
        columns={
            "metric": "Metric",
            "direction": "Direction",
            "same_image_median": "Same image",
            "same_category_median": "Same category",
            "different_category_median": "Different category",
            "passes_expected_order": "Order",
            "oriented_median_difference": r"$\Delta$ median",
            "bootstrap_ci": "95\\% CI",
            "oriented_cliffs_delta": "Cliff's $\\delta$",
            "probability_a_better": "$P(A>B)$",
            "ci_excludes_zero": "CI excludes 0",
        }
    )

    return latex_table.to_latex(
        index=False,
        escape=False,
        longtable=False,
        caption=(
            "MassVis human-human scanpath similarity benchmark for the "
            "encoding phase. The reported difference compares same-image "
            "pairs against different-category pairs and is oriented so that "
            "positive values indicate better same-image similarity."
        ),
        label="tab:massvis-human-similarity",
    )


def format_ci(
    low: float,
    high: float,
    *,
    digits: int = 3,
) -> str:
    return f"[{low:.{digits}f}, {high:.{digits}f}]"


def round_numeric_columns(
    dataframe: pd.DataFrame,
    *,
    digits: int = 4,
) -> pd.DataFrame:
    rounded = dataframe.copy()

    numeric_columns = rounded.select_dtypes(include="number").columns

    for column in numeric_columns:
        rounded[column] = rounded[column].round(digits)

    return rounded


if __name__ == "__main__":
    main()
