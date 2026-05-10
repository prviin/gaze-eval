from __future__ import annotations

import pandas as pd


def split_human_scanpaths_by_subject(
    scanpaths: pd.DataFrame,
    split_ratio: float = 0.5,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split human scanpaths into prediction_part and groundtruth_part.

    The split is done per image_id so that each image has subjects
    in both groups.

    Returns:
        prediction_part, groundtruth_part
    """
    required_columns = {"image_id", "subject_id"}
    missing = required_columns - set(scanpaths.columns)

    if missing:
        raise ValueError(f"scanpaths is missing required columns: {missing}")

    prediction_parts = []
    groundtruth_parts = []

    for image_id, image_group in scanpaths.groupby("image_id"):
        subjects = (
            image_group["subject_id"]
            .drop_duplicates()
            .sample(
                frac=1.0,
                random_state=seed,
            )
        )

        n_prediction = max(1, int(len(subjects) * split_ratio))

        if n_prediction >= len(subjects):
            n_prediction = len(subjects) - 1

        if n_prediction < 1:
            raise ValueError(
                f"Image {image_id} needs at least 2 subjects for human-vs-human split."
            )

        prediction_subjects = set(subjects.iloc[:n_prediction])
        groundtruth_subjects = set(subjects.iloc[n_prediction:])

        prediction_parts.append(
            image_group[image_group["subject_id"].isin(prediction_subjects)]
        )
        groundtruth_parts.append(
            image_group[image_group["subject_id"].isin(groundtruth_subjects)]
        )

    return (
        pd.concat(prediction_parts, ignore_index=True),
        pd.concat(groundtruth_parts, ignore_index=True),
    )
