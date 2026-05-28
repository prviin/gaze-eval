from __future__ import annotations

from pathlib import Path

from gaze_eval.scanpath.human_similarity import evaluate_human_scanpath_similarity
from gaze_eval.scanpath.io import read_scanpath_ndjson
from gaze_eval.scanpath.sanity import (
    check_expected_similarity_order,
    summarize_similarity_by_comparison_type,
)


def main() -> None:
    records = read_scanpath_ndjson(Path("data/processed/ueyes/human_scanpaths.ndjson"))

    # Optional: use a small subset first, because pairwise human-vs-human
    # comparisons can be expensive on the full dataset.
    records = [
        record
        for record in records
        if record.metadata.get("category") in {"poster", "web", "mobile", "desktop"}
    ]

    results = evaluate_human_scanpath_similarity(
        human_scanpaths=records,
        metric_names=[
            "mean_fixation_error",
            "dtw",
            "frechet",
            "hausdorff",
            "number_of_fixations",
        ],
    )

    output_dir = Path("data/processed/ueyes/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    results.to_csv(output_dir / "human_similarity_pairwise.csv", index=False)

    summary = summarize_similarity_by_comparison_type(results)
    summary.to_csv(output_dir / "human_similarity_summary.csv", index=False)

    sanity = check_expected_similarity_order(summary)
    sanity.to_csv(output_dir / "human_similarity_sanity.csv", index=False)

    print("\nSummary:")
    print(summary.to_string(index=False))

    print("\nSanity check:")
    print(sanity.to_string(index=False))


if __name__ == "__main__":
    main()
