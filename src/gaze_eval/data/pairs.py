from __future__ import annotations

import pandas as pd


def make_same_image_human_pairs(
    scanpaths: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create same-image human-vs-human pairs.

    Each row contains:
        prediction_image_id, prediction_subject_id,
        groundtruth_image_id, groundtruth_subject_id,
        pair_type

    Same-image pairs compare different subjects on the same image.
    """
    required_columns = {"image_id", "subject_id"}
    missing = required_columns - set(scanpaths.columns)

    if missing:
        raise ValueError(f"scanpaths is missing required columns: {missing}")

    rows: list[dict[str, str]] = []

    for image_id, image_group in scanpaths.groupby("image_id"):
        subjects = sorted(image_group["subject_id"].unique())

        for pred_subject in subjects:
            for gt_subject in subjects:
                if pred_subject == gt_subject:
                    continue

                rows.append(
                    {
                        "prediction_image_id": image_id,
                        "prediction_subject_id": pred_subject,
                        "groundtruth_image_id": image_id,
                        "groundtruth_subject_id": gt_subject,
                        "pair_type": "same_image",
                    }
                )

    return pd.DataFrame(rows)


def make_different_image_human_pairs(
    scanpaths: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create different-image human-vs-human pairs.

    Different-image pairs compare scanpaths from different images.
    These are used as a negative-control condition.
    """
    required_columns = {"image_id", "subject_id"}
    missing = required_columns - set(scanpaths.columns)

    if missing:
        raise ValueError(f"scanpaths is missing required columns: {missing}")

    image_subjects = (
        scanpaths[["image_id", "subject_id"]]
        .drop_duplicates()
        .sort_values(["image_id", "subject_id"])
    )

    rows: list[dict[str, str]] = []

    for _, pred_row in image_subjects.iterrows():
        for _, gt_row in image_subjects.iterrows():
            if pred_row["image_id"] == gt_row["image_id"]:
                continue

            rows.append(
                {
                    "prediction_image_id": pred_row["image_id"],
                    "prediction_subject_id": pred_row["subject_id"],
                    "groundtruth_image_id": gt_row["image_id"],
                    "groundtruth_subject_id": gt_row["subject_id"],
                    "pair_type": "different_image",
                }
            )

    return pd.DataFrame(rows)
