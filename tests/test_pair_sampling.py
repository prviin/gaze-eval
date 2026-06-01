from __future__ import annotations

from gaze_eval.scanpath.pair_sampling import sample_human_similarity_pairs
from gaze_eval.scanpath.records import Fixation, ScanpathRecord


def make_record(
    *,
    image_id: str,
    subject_id: str,
    category: str,
) -> ScanpathRecord:
    return ScanpathRecord(
        schema_version="gaze-eval-scanpath-v1",
        source="human",
        dataset="test",
        image_id=image_id,
        trial_id=f"{subject_id}_{image_id}",
        subject_id=subject_id,
        coordinate_system={
            "type": "normalized",
            "x_range": [0, 1],
            "y_range": [0, 1],
            "origin": "top_left",
        },
        time_unit="ms",
        duration_unit="ms",
        scanpath=[
            Fixation(
                fixation_index=0,
                timestamp=0.0,
                x=0.1,
                y=0.2,
                duration=100.0,
            ),
            Fixation(
                fixation_index=1,
                timestamp=100.0,
                x=0.3,
                y=0.4,
                duration=120.0,
            ),
        ],
        metadata={"category": category},
    )


def make_records() -> list[ScanpathRecord]:
    records = []

    for image_id, category in [
        ("desktop_1", "desktop"),
        ("desktop_2", "desktop"),
        ("mobile_1", "mobile"),
        ("mobile_2", "mobile"),
    ]:
        for subject_id in ["s01", "s02", "s03"]:
            records.append(
                make_record(
                    image_id=image_id,
                    subject_id=subject_id,
                    category=category,
                )
            )

    return records


def test_sample_human_similarity_pairs_has_all_pair_types() -> None:
    records = make_records()

    pairs = sample_human_similarity_pairs(
        records,
        pairs_per_type=4,
        random_state=42,
        balance_categories=True,
    )

    assert set(pairs["comparison_type"]) == {
        "same_image",
        "same_category",
        "different_category",
    }

    assert pairs["comparison_type"].value_counts().to_dict() == {
        "same_image": 4,
        "same_category": 4,
        "different_category": 4,
    }


def test_sample_human_similarity_pairs_is_reproducible() -> None:
    records = make_records()

    pairs_a = sample_human_similarity_pairs(
        records,
        pairs_per_type=4,
        random_state=42,
        balance_categories=True,
    )

    pairs_b = sample_human_similarity_pairs(
        records,
        pairs_per_type=4,
        random_state=42,
        balance_categories=True,
    )

    assert pairs_a.equals(pairs_b)


def test_sample_human_similarity_pairs_has_no_same_subject_same_image_pairs() -> None:
    records = make_records()

    pairs = sample_human_similarity_pairs(
        records,
        pairs_per_type=10,
        random_state=42,
        balance_categories=True,
    )

    invalid = pairs[
        (pairs["image_id_a"] == pairs["image_id_b"])
        & (pairs["subject_id_a"] == pairs["subject_id_b"])
    ]

    assert invalid.empty


def test_sample_human_similarity_pairs_adds_category_pair_column() -> None:
    records = make_records()

    pairs = sample_human_similarity_pairs(
        records,
        pairs_per_type=4,
        random_state=42,
        balance_categories=True,
    )

    assert "category_pair" in pairs.columns

    different_category_pairs = pairs[pairs["comparison_type"] == "different_category"]

    assert set(different_category_pairs["category_pair"]) == {
        "desktop-mobile",
    }


def test_same_image_pairs_are_same_image_different_subjects() -> None:
    records = make_records()

    pairs = sample_human_similarity_pairs(
        records,
        pairs_per_type=10,
        random_state=42,
        balance_categories=True,
    )

    same_image_pairs = pairs[pairs["comparison_type"] == "same_image"]

    assert not same_image_pairs.empty
    assert (same_image_pairs["image_id_a"] == same_image_pairs["image_id_b"]).all()
    assert (same_image_pairs["subject_id_a"] != same_image_pairs["subject_id_b"]).all()


def test_same_category_pairs_are_different_images_same_category() -> None:
    records = make_records()

    pairs = sample_human_similarity_pairs(
        records,
        pairs_per_type=10,
        random_state=42,
        balance_categories=True,
    )

    same_category_pairs = pairs[pairs["comparison_type"] == "same_category"]

    assert not same_category_pairs.empty
    assert (
        same_category_pairs["image_id_a"] != same_category_pairs["image_id_b"]
    ).all()
    assert (
        same_category_pairs["category_a"] == same_category_pairs["category_b"]
    ).all()


def test_different_category_pairs_are_different_categories() -> None:
    records = make_records()

    pairs = sample_human_similarity_pairs(
        records,
        pairs_per_type=10,
        random_state=42,
        balance_categories=True,
    )

    different_category_pairs = pairs[pairs["comparison_type"] == "different_category"]

    assert not different_category_pairs.empty
    assert (
        different_category_pairs["category_a"] != different_category_pairs["category_b"]
    ).all()
