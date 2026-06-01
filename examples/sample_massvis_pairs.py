from pathlib import Path

from gaze_eval.scanpath.io import read_scanpath_ndjson
from gaze_eval.scanpath.pair_sampling import (
    sample_human_similarity_pairs,
    save_pair_sample,
)


def main() -> None:
    phase = "enc"

    records_path = Path(f"data/processed/massvis/{phase}/human_scanpaths.ndjson")
    output_path = Path(f"data/processed/massvis/{phase}/pairs/massvis_pairs_seed42.csv")

    records = read_scanpath_ndjson(records_path)

    pairs = sample_human_similarity_pairs(
        records,
        pairs_per_type=10_000,
        random_state=42,
        balance_categories=True,
    )

    save_pair_sample(pairs, output_path)

    print(f"Phase: {phase}")
    print(f"Loaded records: {len(records)}")
    print(f"Saved pairs: {len(pairs)}")
    print(f"Output: {output_path}")

    print("\nPair counts:")
    print(pairs["comparison_type"].value_counts())

    print("\nCategory-pair counts:")
    print(pairs.groupby(["comparison_type", "category_pair"]).size())


if __name__ == "__main__":
    main()
