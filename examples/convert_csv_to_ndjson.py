from __future__ import annotations

from pathlib import Path

from gaze_eval.scanpath.convert import (
    convert_human_csv_to_ndjson,
    convert_prediction_csv_to_ndjson,
)


def main() -> None:
    data_dir = Path("tests/data/debug")

    convert_human_csv_to_ndjson(
        data_dir / "human_scanpaths.csv",
        data_dir / "human_scanpaths_from_csv.ndjson",
        dataset="debug",
    )

    convert_prediction_csv_to_ndjson(
        data_dir / "pred_good.csv",
        data_dir / "pred_good_from_csv.ndjson",
        dataset="debug",
    )

    print("Wrote:")
    print(data_dir / "human_scanpaths_from_csv.ndjson")
    print(data_dir / "pred_good_from_csv.ndjson")


if __name__ == "__main__":
    main()
