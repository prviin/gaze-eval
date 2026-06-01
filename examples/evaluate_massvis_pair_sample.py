from __future__ import annotations

from pathlib import Path

from gaze_eval.scanpath.human_similarity import evaluate_human_pair_sample
from gaze_eval.scanpath.io import read_scanpath_ndjson
from gaze_eval.scanpath.pair_sampling import load_pair_sample
from gaze_eval.scanpath.statistics import (
    BootstrapConfig,
    analyze_metric_group_differences,
    check_expected_similarity_order,
    compute_human_baseline_quality_scores,
    summarize_metric_distributions,
)


def main() -> None:
    phase = "enc"

    records_path = Path(f"data/processed/massvis/{phase}/human_scanpaths.ndjson")
    pairs_path = Path(f"data/processed/massvis/{phase}/pairs/massvis_pairs_seed42.csv")
    output_dir = Path(f"data/processed/massvis/{phase}/results")

    results_path = output_dir / "massvis_pair_metric_results_seed42.csv"
    summary_path = output_dir / "massvis_pair_metric_summary_seed42.csv"
    sanity_path = output_dir / "massvis_pair_metric_sanity_seed42.csv"
    differences_path = output_dir / "massvis_pair_metric_differences_seed42.csv"
    baseline_path = output_dir / "massvis_human_baseline_quality_seed42.csv"

    output_dir.mkdir(parents=True, exist_ok=True)

    records = read_scanpath_ndjson(records_path)
    pairs = load_pair_sample(pairs_path)

    results = evaluate_human_pair_sample(
        records=records,
        pairs=pairs,
    )

    results.to_csv(results_path, index=False)

    summary = summarize_metric_distributions(results)
    summary.to_csv(summary_path, index=False)

    sanity = check_expected_similarity_order(summary)
    sanity.to_csv(sanity_path, index=False)

    differences = analyze_metric_group_differences(
        results,
        bootstrap=BootstrapConfig(
            n_bootstrap=5000,
            confidence_level=0.95,
            random_state=42,
        ),
    )
    differences.to_csv(differences_path, index=False)

    baseline = compute_human_baseline_quality_scores(summary)
    baseline.to_csv(baseline_path, index=False)

    print(f"Phase: {phase}")
    print(f"Saved results: {results_path}")
    print(f"Saved summary: {summary_path}")
    print(f"Saved sanity: {sanity_path}")
    print(f"Saved differences: {differences_path}")
    print(f"Saved human baseline: {baseline_path}")

    print("\nSummary:")
    print(summary.to_string(index=False))

    print("\nSanity:")
    print(sanity.to_string(index=False))


if __name__ == "__main__":
    main()
