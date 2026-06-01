from __future__ import annotations

from collections import Counter
from pathlib import Path

from gaze_eval.datasets.massvis import convert_massvis_to_ndjson, load_massvis
from gaze_eval.scanpath.io import read_scanpath_ndjson


def main() -> None:
    root = Path("data/masviss_data")

    for phase in ["enc", "rec", "both"]:
        output_path = Path(f"data/processed/massvis/{phase}/human_scanpaths.ndjson")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        records = load_massvis(
            root=root,
            phase=phase,
            normalize_coordinates=True,
            out_of_bounds="drop",
            drop_missing_stimuli=True,
            # max_files=10,
        )

        print(f"\nPhase: {phase}")
        print(f"Loaded {len(records)} records for quick check")

        if records:
            first = records[0]
            print("First record:")
            print("  dataset:", first.dataset)
            print("  image_id:", first.image_id)
            print("  subject_id:", first.subject_id)
            print("  phase:", first.metadata.get("phase"))
            print("  category:", first.metadata.get("category"))
            print("  vistype:", first.metadata.get("vistype"))
            print("  number of fixations:", len(first.scanpath))
            print("  first fixation:", first.scanpath[0])

        convert_massvis_to_ndjson(
            root=root,
            output_path=output_path,
            phase=phase,
            normalize_coordinates=True,
            out_of_bounds="drop",
            drop_missing_stimuli=True,
        )

        print(f"Wrote {output_path}")

        summarize_output(output_path, phase=phase)


def summarize_output(path: Path, *, phase: str) -> None:
    records = read_scanpath_ndjson(path)

    print(f"\nSummary for phase: {phase}")
    print("  records:", len(records))
    print("  subjects:", len({record.subject_id for record in records}))
    print("  images:", len({record.image_id for record in records}))
    print(
        "  categories:", Counter(record.metadata.get("category") for record in records)
    )
    print("  phases:", Counter(record.metadata.get("phase") for record in records))

    lengths = [len(record.scanpath) for record in records]

    if lengths:
        print(
            "  fixations min/mean/max:",
            min(lengths),
            sum(lengths) / len(lengths),
            max(lengths),
        )


if __name__ == "__main__":
    main()
