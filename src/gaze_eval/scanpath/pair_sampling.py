from __future__ import annotations

import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

from gaze_eval.scanpath.records import ScanpathRecord
from tqdm.auto import tqdm

Pair = tuple[ScanpathRecord, ScanpathRecord, str]


def sample_human_similarity_pairs(
    records: list[ScanpathRecord],
    *,
    pairs_per_type: int,
    random_state: int = 42,
    balance_categories: bool = True,
) -> pd.DataFrame:
    """
    Sample reproducible human-human scanpath pairs.

    Pair types:
        same_image:
            Same image, different subjects.

        same_category:
            Different images from the same category.

        different_category:
            Different images from different categories.

    Returns
    -------
    pd.DataFrame
        A reproducible pair table. Save this table and reuse it for evaluation.
    """
    rng = random.Random(random_state)

    same_image_pairs = build_same_image_pairs(records)
    same_category_pairs = build_same_category_pairs(records)
    different_category_pairs = build_different_category_pairs(records)

    if balance_categories:
        same_image_sample = sample_balanced_by_category(
            same_image_pairs,
            pairs_per_type=pairs_per_type,
            random_state=random_state,
        )

        same_category_sample = sample_balanced_by_category(
            same_category_pairs,
            pairs_per_type=pairs_per_type,
            random_state=random_state + 1,
        )

        different_category_sample = sample_balanced_by_category_pair(
            different_category_pairs,
            pairs_per_type=pairs_per_type,
            random_state=random_state + 2,
        )
    else:
        same_image_sample = sample_pairs(
            same_image_pairs,
            n=pairs_per_type,
            rng=rng,
        )
        same_category_sample = sample_pairs(
            same_category_pairs,
            n=pairs_per_type,
            rng=rng,
        )
        different_category_sample = sample_pairs(
            different_category_pairs,
            n=pairs_per_type,
            rng=rng,
        )

    all_pairs = same_image_sample + same_category_sample + different_category_sample

    rows = []

    for pair_id, (record_a, record_b, comparison_type) in enumerate(all_pairs):
        category_a = record_a.metadata.get("category")
        category_b = record_b.metadata.get("category")

        rows.append(
            {
                "pair_id": pair_id,
                "comparison_type": comparison_type,
                "image_id_a": record_a.image_id,
                "subject_id_a": record_a.subject_id,
                "trial_id_a": record_a.trial_id,
                "category_a": category_a,
                "image_id_b": record_b.image_id,
                "subject_id_b": record_b.subject_id,
                "trial_id_b": record_b.trial_id,
                "category_b": category_b,
                "category_pair": make_category_pair(category_a, category_b),
                "random_state": random_state,
                "sampling_version": "v1",
            }
        )

    return pd.DataFrame(rows)


def build_same_image_pairs(records: list[ScanpathRecord]) -> list[Pair]:
    by_image: dict[str, list[ScanpathRecord]] = defaultdict(list)

    for record in records:
        validate_human_record(record)
        by_image[record.image_id].append(record)

    pairs: list[Pair] = []

    for image_records in tqdm(
        by_image.values(),
        desc="Building same-image pairs",
        unit="image",
    ):
        for index_a in range(len(image_records)):
            for index_b in range(index_a + 1, len(image_records)):
                record_a = image_records[index_a]
                record_b = image_records[index_b]

                if record_a.subject_id == record_b.subject_id:
                    continue

                pairs.append((record_a, record_b, "same_image"))

    return pairs


def build_same_category_pairs(records: list[ScanpathRecord]) -> list[Pair]:
    by_category: dict[str, list[ScanpathRecord]] = defaultdict(list)

    for record in records:
        validate_human_record(record)

        category = record.metadata.get("category")
        if category is None:
            continue

        by_category[str(category)].append(record)

    pairs: list[Pair] = []

    for category_records in tqdm(
        by_category.values(),
        desc="Building same-category pairs",
        unit="category",
    ):
        for index_a in range(len(category_records)):
            for index_b in range(index_a + 1, len(category_records)):
                record_a = category_records[index_a]
                record_b = category_records[index_b]

                if record_a.image_id == record_b.image_id:
                    continue

                pairs.append((record_a, record_b, "same_category"))

    return pairs


def build_different_category_pairs(records: list[ScanpathRecord]) -> list[Pair]:
    records_with_category = [
        record for record in records if record.metadata.get("category") is not None
    ]

    pairs: list[Pair] = []

    for index_a in range(len(records_with_category)):
        for index_b in range(index_a + 1, len(records_with_category)):
            record_a = records_with_category[index_a]
            record_b = records_with_category[index_b]

            category_a = record_a.metadata.get("category")
            category_b = record_b.metadata.get("category")

            if category_a == category_b:
                continue

            pairs.append((record_a, record_b, "different_category"))

    return pairs


def sample_pairs(
    pairs: list[Pair],
    *,
    n: int,
    rng: random.Random,
) -> list[Pair]:
    if len(pairs) <= n:
        return pairs

    return rng.sample(pairs, n)


def sample_balanced_by_category(
    pairs: list[Pair],
    *,
    pairs_per_type: int,
    random_state: int,
) -> list[Pair]:
    rng = random.Random(random_state)

    by_category: dict[str, list[Pair]] = defaultdict(list)

    for pair in pairs:
        record_a, _, _ = pair
        category = record_a.metadata.get("category")

        if category is None:
            continue

        by_category[str(category)].append(pair)

    if not by_category:
        return sample_pairs(pairs, n=pairs_per_type, rng=rng)

    categories = sorted(by_category)
    per_category = pairs_per_type // len(categories)
    remainder = pairs_per_type % len(categories)

    sampled: list[Pair] = []

    for index, category in enumerate(categories):
        n = per_category + (1 if index < remainder else 0)
        sampled.extend(sample_pairs(by_category[category], n=n, rng=rng))

    return sampled


def sample_balanced_by_category_pair(
    pairs: list[Pair],
    *,
    pairs_per_type: int,
    random_state: int,
) -> list[Pair]:
    rng = random.Random(random_state)

    by_category_pair: dict[tuple[str, str], list[Pair]] = defaultdict(list)

    for pair in pairs:
        record_a, record_b, _ = pair

        category_a = str(record_a.metadata.get("category"))
        category_b = str(record_b.metadata.get("category"))

        category_pair = tuple(sorted((category_a, category_b)))
        by_category_pair[category_pair].append(pair)

    if not by_category_pair:
        return sample_pairs(pairs, n=pairs_per_type, rng=rng)

    category_pairs = sorted(by_category_pair)
    per_category_pair = pairs_per_type // len(category_pairs)
    remainder = pairs_per_type % len(category_pairs)

    sampled: list[Pair] = []

    for index, category_pair in enumerate(category_pairs):
        n = per_category_pair + (1 if index < remainder else 0)
        sampled.extend(
            sample_pairs(
                by_category_pair[category_pair],
                n=n,
                rng=rng,
            )
        )

    return sampled


def save_pair_sample(pairs: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(path, index=False)


def load_pair_sample(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def validate_human_record(record: ScanpathRecord) -> None:
    if record.source != "human":
        raise ValueError("all records must have source='human'")

    if record.subject_id is None:
        raise ValueError("human record is missing subject_id")


def make_category_pair(
    category_a: object,
    category_b: object,
) -> str:
    categories = sorted([str(category_a), str(category_b)])
    return f"{categories[0]}-{categories[1]}"
