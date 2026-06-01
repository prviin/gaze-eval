from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


RESULTS_PATH = Path("data/processed/ueyes/results/ueyes_pair_metric_results_seed42.csv")
OUTPUT_DIR = Path("data/processed/ueyes/figures")

COMPARISON_ORDER = [
    "same_image",
    "same_category",
    "different_category",
]

COMPARISON_LABELS = {
    "same_image": "Same image",
    "same_category": "Same category",
    "different_category": "Different category",
}

DEFAULT_METRICS = [
    "eyenalysis",
    "dtw",
    "scanmatch",
    "mean_fixation_error",
    "multimatch_position",
    "multimatch_duration",
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = pd.read_csv(RESULTS_PATH)

    metrics = sorted(
        metric
        for metric in results["metric"].dropna().unique()
        if results.loc[results["metric"] == metric, "direction"].iloc[0]
        in {"lower", "higher"}
    )

    for metric in metrics:
        plot_metric_distribution(
            results=results,
            metric=metric,
            output_dir=OUTPUT_DIR,
        )

    plot_expected_order_effects(
        paper_table_path=Path(
            "data/processed/ueyes/paper_tables/ueyes_main_metric_table.csv"
        ),
        output_path=OUTPUT_DIR / "ueyes_expected_order_effects.png",
    )

    print(f"Saved figures to: {OUTPUT_DIR}")


def plot_metric_distribution(
    *,
    results: pd.DataFrame,
    metric: str,
    output_dir: Path,
) -> None:
    metric_data = results[
        (results["metric"] == metric)
        & (results["comparison_type"].isin(COMPARISON_ORDER))
    ].copy()

    metric_data = metric_data.dropna(subset=["value"])

    if metric_data.empty:
        print(f"Skipping {metric}: no valid values")
        return

    direction = str(metric_data["direction"].iloc[0])

    values_by_group = [
        metric_data.loc[
            metric_data["comparison_type"] == comparison_type,
            "value",
        ].to_numpy()
        for comparison_type in COMPARISON_ORDER
    ]

    labels = [COMPARISON_LABELS[item] for item in COMPARISON_ORDER]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))

    box = ax.boxplot(
        values_by_group,
        tick_labels=labels,
        showfliers=False,
        patch_artist=True,
    )

    for patch in box["boxes"]:
        patch.set_alpha(0.35)

    ax.set_title(format_metric_name(metric), pad=14)
    ax.set_ylabel("Metric value")
    ax.set_xlabel("Pair type")

    if direction == "lower":
        note = "Lower values indicate higher similarity."
    elif direction == "higher":
        note = "Higher values indicate higher similarity."
    else:
        note = "Descriptive metric."

    fig.text(
        0.5,
        0.01,
        note,
        ha="center",
        va="bottom",
        fontsize=9,
    )

    fig.tight_layout(rect=(0, 0.04, 1, 1))

    output_path = output_dir / f"ueyes_distribution_{metric}.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved {output_path}")


def plot_expected_order_effects(
    *,
    paper_table_path: Path,
    output_path: Path,
) -> None:
    if not paper_table_path.exists():
        print(f"Skipping effect plot: missing {paper_table_path}")
        return

    table = pd.read_csv(paper_table_path)

    table = table.dropna(subset=["oriented_cliffs_delta"]).copy()

    if table.empty:
        print("Skipping effect plot: no effect sizes")
        return

    table = table.sort_values("oriented_cliffs_delta", ascending=True)

    fig_height = max(5.5, 0.36 * len(table))
    fig, ax = plt.subplots(figsize=(8.5, fig_height))

    ax.barh(
        table["metric"].map(format_metric_name),
        table["oriented_cliffs_delta"],
    )

    ax.axvline(0.0, linewidth=1.0)

    ax.set_xlabel("Oriented Cliff's delta")
    ax.set_ylabel("Metric")
    ax.set_title("UEyes expected-order effect sizes", pad=14)

    fig.text(
        0.5,
        0.01,
        "Positive values indicate stronger same-image than different-category similarity.",
        ha="center",
        va="bottom",
        fontsize=9,
    )

    fig.tight_layout(rect=(0, 0.035, 1, 1))

    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved {output_path}")


def format_metric_name(metric: str) -> str:
    special_names = {
        "dtw": "DTW",
        "tde": "TDE",
        "scaled_tde": "Scaled TDE",
        "corm": "CORM",
        "eyenalysis": "EyeNalysis",
    }

    if metric in special_names:
        return special_names[metric]

    return metric.replace("_", " ").title()


if __name__ == "__main__":
    main()
