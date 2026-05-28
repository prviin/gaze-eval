from __future__ import annotations

from pathlib import Path

from gaze_eval.datasets.ueyes import convert_ueyes_to_ndjson, load_ueyes


def main() -> None:
    root = Path("data/Ueyes/UEyes_dataset")
    output_path = Path("data/processed/ueyes/human_scanpaths.ndjson")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = load_ueyes(root, max_files=10)

    print(f"Loaded {len(records)} records for quick check")

    first = records[0]
    print("First record:")
    print("  dataset:", first.dataset)
    print("  image_id:", first.image_id)
    print("  subject_id:", first.subject_id)
    print("  split:", first.split)
    print("  category:", first.metadata.get("category"))
    print("  number of fixations:", len(first.scanpath))
    print("  first fixation:", first.scanpath[0])

    convert_ueyes_to_ndjson(
        root=root,
        output_path=output_path,
    )

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
