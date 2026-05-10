from __future__ import annotations

import numpy as np
import pandas as pd
from collections import Counter

from gaze_eval.scanpath.registry import ScanpathMetric


def _sort_scanpath(scanpath: pd.DataFrame) -> pd.DataFrame:
    """
    Sort a scanpath by fixation_index.

    The expected input format is:
        image_id, subject_id, fixation_index, x, y, duration

    For predicted scanpaths, subject_id may be absent.
    """
    if "fixation_index" not in scanpath.columns:
        raise ValueError("scanpath must contain a 'fixation_index' column.")

    return scanpath.sort_values("fixation_index")


def _to_xy(scanpath: pd.DataFrame) -> np.ndarray:
    """
    Convert a scanpath DataFrame to an array of normalized fixation coordinates.

    Returns:
        Array with shape (n_fixations, 2), where columns are x and y.
    """
    required_columns = {"x", "y"}
    missing = required_columns - set(scanpath.columns)

    if missing:
        raise ValueError(f"scanpath is missing required columns: {missing}")

    scanpath = _sort_scanpath(scanpath)

    return scanpath[["x", "y"]].to_numpy(dtype=float)


def _to_duration(scanpath: pd.DataFrame) -> np.ndarray:
    """
    Convert fixation durations to a numpy array.

    Invalid durations are removed later by metric-specific functions.
    """
    if "duration" not in scanpath.columns:
        raise ValueError("scanpath must contain a 'duration' column.")

    scanpath = _sort_scanpath(scanpath)

    return scanpath["duration"].to_numpy(dtype=float)


def _truncate_pair(
    a: np.ndarray,
    b: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Truncate two arrays to the same minimum length.

    This is useful when predicted and ground-truth scanpaths have different lengths.
    """
    n = min(len(a), len(b))

    if n == 0:
        return a[:0], b[:0]

    return a[:n], b[:n]


def _to_multimatch_fix_vector(
    scanpath: pd.DataFrame,
    width: int = 1000,
    height: int = 1000,
) -> np.recarray:
    """
    Convert a scanpath DataFrame to the input format expected by multimatch-gaze.

    multimatch-gaze expects an array with:
        start_x, start_y, duration

    Coordinates should be in pixels.
    Durations should be in seconds.

    Our internal convention:
        x, y are normalized to [0, 1]
        duration is in milliseconds
    """
    scanpath = _sort_scanpath(scanpath)

    x_px = scanpath["x"].to_numpy(dtype=float) * width
    y_px = scanpath["y"].to_numpy(dtype=float) * height

    if "duration" in scanpath.columns:
        duration_ms = scanpath["duration"].to_numpy(dtype=float)
        duration_sec = np.where(duration_ms >= 0, duration_ms / 1000.0, 0.2)
    else:
        duration_sec = np.full(len(scanpath), 0.2, dtype=float)

    fix_vector = np.rec.fromarrays(
        [x_px, y_px, duration_sec],
        names=["start_x", "start_y", "duration"],
    )

    return fix_vector


def euclidean_distances(
    pred_xy: np.ndarray,
    gt_xy: np.ndarray,
) -> np.ndarray:
    """
    Compute Euclidean distances between corresponding fixation points.
    """
    pred_xy, gt_xy = _truncate_pair(pred_xy, gt_xy)

    if len(pred_xy) == 0:
        return np.array([])

    return np.linalg.norm(pred_xy - gt_xy, axis=1)


def mean_fixation_error(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Mean Euclidean distance between corresponding predicted and human fixations.

    Coordinates are expected to be normalized to [0, 1].

    Lower is better.
    """
    distances = euclidean_distances(
        pred_xy=_to_xy(pred),
        gt_xy=_to_xy(gt),
    )

    if len(distances) == 0:
        return np.nan

    return float(np.mean(distances))


def final_fixation_error(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Euclidean distance between the final predicted fixation and final human fixation.

    Lower is better.
    """
    pred_xy = _to_xy(pred)
    gt_xy = _to_xy(gt)

    if len(pred_xy) == 0 or len(gt_xy) == 0:
        return np.nan

    return float(np.linalg.norm(pred_xy[-1] - gt_xy[-1]))


def saccade_vectors(xy: np.ndarray) -> np.ndarray:
    """
    Compute saccade vectors from fixation coordinates.

    If the scanpath has n fixations, it has n - 1 saccades.

    Returns:
        Array with shape (n_saccades, 2).
    """
    if len(xy) < 2:
        return np.empty((0, 2), dtype=float)

    return np.diff(xy, axis=0)


def saccade_amplitudes(xy: np.ndarray) -> np.ndarray:
    """
    Compute saccade amplitudes, i.e. lengths of movement vectors.
    """
    vectors = saccade_vectors(xy)

    if len(vectors) == 0:
        return np.array([])

    return np.linalg.norm(vectors, axis=1)


def mean_saccade_amplitude_error(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Mean absolute error between predicted and human saccade amplitudes.

    Lower is better.
    """
    pred_amp = saccade_amplitudes(_to_xy(pred))
    gt_amp = saccade_amplitudes(_to_xy(gt))

    pred_amp, gt_amp = _truncate_pair(pred_amp, gt_amp)

    if len(pred_amp) == 0:
        return np.nan

    errors = np.abs(pred_amp - gt_amp)

    return float(np.mean(errors))


def saccade_angles(xy: np.ndarray) -> np.ndarray:
    """
    Compute saccade angles in radians.

    Angle is computed with atan2(dy, dx), so values are in [-pi, pi].
    """
    vectors = saccade_vectors(xy)

    if len(vectors) == 0:
        return np.array([])

    return np.arctan2(vectors[:, 1], vectors[:, 0])


def angular_difference(
    a: np.ndarray,
    b: np.ndarray,
) -> np.ndarray:
    """
    Compute the smallest absolute angular difference between two angle arrays.

    Output range is [0, pi].
    """
    a, b = _truncate_pair(a, b)

    if len(a) == 0:
        return np.array([])

    diff = np.abs(a - b)

    return np.minimum(diff, 2 * np.pi - diff)


def mean_saccade_angle_error(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Mean angular difference between predicted and human saccade directions.

    Unit:
        Radians.

    Range:
        [0, pi]

    Lower is better.
    """
    pred_angles = saccade_angles(_to_xy(pred))
    gt_angles = saccade_angles(_to_xy(gt))

    errors = angular_difference(pred_angles, gt_angles)

    if len(errors) == 0:
        return np.nan

    return float(np.mean(errors))


def mean_duration_error(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Mean absolute error between predicted and human fixation durations.

    Durations are expected to be in milliseconds.

    Lower is better.

    Invalid durations such as -1 are ignored.
    """
    pred_duration = _to_duration(pred)
    gt_duration = _to_duration(gt)

    pred_duration, gt_duration = _truncate_pair(pred_duration, gt_duration)

    if len(pred_duration) == 0:
        return np.nan

    valid_mask = (pred_duration >= 0) & (gt_duration >= 0)

    if not np.any(valid_mask):
        return np.nan

    errors = np.abs(pred_duration[valid_mask] - gt_duration[valid_mask])

    return float(np.mean(errors))


def duration_correlation(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Pearson correlation between predicted and human fixation durations.

    Higher is better.

    Returns NaN if:
        - fewer than 2 valid duration pairs exist
        - one sequence has zero variance
    """
    pred_duration = _to_duration(pred)
    gt_duration = _to_duration(gt)

    pred_duration, gt_duration = _truncate_pair(pred_duration, gt_duration)

    if len(pred_duration) < 2:
        return np.nan

    valid_mask = (pred_duration >= 0) & (gt_duration >= 0)

    pred_valid = pred_duration[valid_mask]
    gt_valid = gt_duration[valid_mask]

    if len(pred_valid) < 2:
        return np.nan

    if np.isclose(np.std(pred_valid), 0.0) or np.isclose(np.std(gt_valid), 0.0):
        return np.nan

    return float(np.corrcoef(pred_valid, gt_valid)[0, 1])


def simple_dtw_distance(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Simple Dynamic Time Warping distance over normalized x,y fixation coordinates.

    This is not a point-wise metric, but we keep it here for now
    until we separate alignment metrics into another file.

    Lower is better.
    """
    a = _to_xy(pred)
    b = _to_xy(gt)

    if len(a) == 0 or len(b) == 0:
        return np.nan

    dp = np.full((len(a) + 1, len(b) + 1), np.inf)
    dp[0, 0] = 0.0

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = np.linalg.norm(a[i - 1] - b[j - 1])
            dp[i, j] = cost + min(
                dp[i - 1, j],
                dp[i, j - 1],
                dp[i - 1, j - 1],
            )

    return float(dp[len(a), len(b)] / (len(a) + len(b)))


def pairwise_distances(
    a: np.ndarray,
    b: np.ndarray,
) -> np.ndarray:
    """
    Pairwise Euclidean distance matrix between two scanpaths.

    Args:
        a: Array of shape (n, 2).
        b: Array of shape (m, 2).

    Returns:
        Array of shape (n, m), where entry (i, j) is the distance
        between a[i] and b[j].
    """
    if len(a) == 0 or len(b) == 0:
        return np.empty((len(a), len(b)))

    diff = a[:, None, :] - b[None, :, :]
    return np.linalg.norm(diff, axis=2)


def dtw_distance(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Dynamic Time Warping distance over fixation coordinates.

    DTW finds a low-cost alignment between two fixation sequences.
    It is useful when two scanpaths have similar order but different
    local timing or different numbers of fixations.

    Lower is better.
    """
    a = _to_xy(pred)
    b = _to_xy(gt)

    if len(a) == 0 or len(b) == 0:
        return np.nan

    distances = pairwise_distances(a, b)

    dp = np.full((len(a) + 1, len(b) + 1), np.inf)
    dp[0, 0] = 0.0

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = distances[i - 1, j - 1]
            dp[i, j] = cost + min(
                dp[i - 1, j],
                dp[i, j - 1],
                dp[i - 1, j - 1],
            )

    return float(dp[len(a), len(b)] / (len(a) + len(b)))


def discrete_frechet_distance(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Discrete Fréchet distance between two fixation sequences.

    Intuition:
        Measures how far apart two ordered paths are when both paths
        are traversed from start to end.

    Difference from DTW:
        DTW accumulates alignment cost.
        Fréchet measures the worst aligned distance along the best traversal.

    Lower is better.
    """
    a = _to_xy(pred)
    b = _to_xy(gt)

    if len(a) == 0 or len(b) == 0:
        return np.nan

    distances = pairwise_distances(a, b)

    ca = np.full((len(a), len(b)), -1.0)

    def compute(i: int, j: int) -> float:
        if ca[i, j] > -1:
            return ca[i, j]

        if i == 0 and j == 0:
            ca[i, j] = distances[i, j]
        elif i > 0 and j == 0:
            ca[i, j] = max(compute(i - 1, 0), distances[i, j])
        elif i == 0 and j > 0:
            ca[i, j] = max(compute(0, j - 1), distances[i, j])
        elif i > 0 and j > 0:
            ca[i, j] = max(
                min(
                    compute(i - 1, j),
                    compute(i - 1, j - 1),
                    compute(i, j - 1),
                ),
                distances[i, j],
            )
        else:
            ca[i, j] = np.inf

        return ca[i, j]

    return float(compute(len(a) - 1, len(b) - 1))


def hausdorff_distance(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Symmetric Hausdorff distance between two sets of fixation points.

    It measures the largest nearest-neighbor mismatch between two scanpaths.

    Important:
        This metric ignores fixation order.

    Lower is better.
    """
    a = _to_xy(pred)
    b = _to_xy(gt)

    if len(a) == 0 or len(b) == 0:
        return np.nan

    distances = pairwise_distances(a, b)

    forward = np.max(np.min(distances, axis=1))
    backward = np.max(np.min(distances, axis=0))

    return float(max(forward, backward))


def multimatch_components_exact(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    width: int = 1000,
    height: int = 1000,
    grouping: bool = True,
    direction_threshold: float = 45.0,
    duration_threshold: float = 0.3,
    amplitude_threshold: float | None = None,
) -> dict[str, float]:
    """
    Compute MultiMatch using the `multimatch-gaze` Python package.

    This is the proper MultiMatch implementation, not the simplified version.

    Returns:
        {
            "multimatch_shape": float,
            "multimatch_direction": float,
            "multimatch_length": float,
            "multimatch_position": float,
            "multimatch_duration": float,
        }

    Notes:
        - Coordinates are converted from normalized [0, 1] to pixels.
        - Durations are converted from milliseconds to seconds.
        - If amplitude_threshold is None, it is set to 10% of the screen diagonal,
          following the default value described for the original MultiMatch toolbox.
    """
    try:
        import multimatch_gaze as m
    except ImportError as exc:
        raise ImportError(
            "MultiMatch requires the `multimatch-gaze` package. "
            "Install it with: pip install multimatch-gaze"
        ) from exc

    if amplitude_threshold is None:
        amplitude_threshold = 0.10 * float(np.sqrt(width**2 + height**2))

    pred_fix = _to_multimatch_fix_vector(pred, width=width, height=height)
    gt_fix = _to_multimatch_fix_vector(gt, width=width, height=height)

    if len(pred_fix) < 2 or len(gt_fix) < 2:
        return {
            "multimatch_shape": np.nan,
            "multimatch_direction": np.nan,
            "multimatch_length": np.nan,
            "multimatch_position": np.nan,
            "multimatch_duration": np.nan,
        }

    scores = m.docomparison(
        pred_fix,
        gt_fix,
        screensize=[width, height],
        grouping=grouping,
        TDir=direction_threshold,
        TDur=duration_threshold,
        TAmp=amplitude_threshold,
    )

    scores = np.asarray(scores, dtype=float).squeeze()

    return {
        "multimatch_shape": float(scores[0]),
        "multimatch_direction": float(scores[1]),
        "multimatch_length": float(scores[2]),
        "multimatch_position": float(scores[3]),
        "multimatch_duration": float(scores[4]),
    }


def multimatch_shape(pred: pd.DataFrame, gt: pd.DataFrame) -> float:
    return multimatch_components_exact(pred, gt)["multimatch_shape"]


def multimatch_direction(pred: pd.DataFrame, gt: pd.DataFrame) -> float:
    return multimatch_components_exact(pred, gt)["multimatch_direction"]


def multimatch_length(pred: pd.DataFrame, gt: pd.DataFrame) -> float:
    return multimatch_components_exact(pred, gt)["multimatch_length"]


def multimatch_position(pred: pd.DataFrame, gt: pd.DataFrame) -> float:
    return multimatch_components_exact(pred, gt)["multimatch_position"]


def multimatch_duration(pred: pd.DataFrame, gt: pd.DataFrame) -> float:
    return multimatch_components_exact(pred, gt)["multimatch_duration"]


# ---------------------------------------------------------------------
# Symbolic / AOI-based metrics
# ---------------------------------------------------------------------


def scanpath_to_aoi_sequence(
    scanpath: pd.DataFrame,
    x_bins: int = 12,
    y_bins: int = 8,
) -> list[int]:
    """
    Convert a scanpath into a symbolic AOI/grid sequence.

    The image is divided into x_bins by y_bins cells.
    Each fixation is assigned to one grid cell.

    Coordinates are expected to be normalized to [0, 1].

    Returns:
        A list of integer AOI IDs.
    """
    xy = _to_xy(scanpath)

    if len(xy) == 0:
        return []

    eps = np.finfo(float).eps

    x = np.clip(xy[:, 0], 0.0, 1.0 - eps)
    y = np.clip(xy[:, 1], 0.0, 1.0 - eps)

    x_idx = np.floor(x * x_bins).astype(int)
    y_idx = np.floor(y * y_bins).astype(int)

    return (y_idx * x_bins + x_idx).tolist()


def levenshtein_distance_from_sequences(
    seq_a: list[int],
    seq_b: list[int],
) -> int:
    """
    Compute Levenshtein edit distance between two AOI sequences.

    Operations:
        insertion
        deletion
        substitution

    Lower is better.
    """
    n = len(seq_a)
    m = len(seq_b)

    if n == 0:
        return m

    if m == 0:
        return n

    dp = np.zeros((n + 1, m + 1), dtype=int)

    dp[:, 0] = np.arange(n + 1)
    dp[0, :] = np.arange(m + 1)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            substitution_cost = 0 if seq_a[i - 1] == seq_b[j - 1] else 1

            dp[i, j] = min(
                dp[i - 1, j] + 1,
                dp[i, j - 1] + 1,
                dp[i - 1, j - 1] + substitution_cost,
            )

    return int(dp[n, m])


def levenshtein_distance_metric(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    x_bins: int = 12,
    y_bins: int = 8,
) -> float:
    """
    Levenshtein distance between predicted and human AOI sequences.

    The scanpaths are first converted to grid/AOI sequences.

    Lower is better.
    """
    pred_seq = scanpath_to_aoi_sequence(pred, x_bins=x_bins, y_bins=y_bins)
    gt_seq = scanpath_to_aoi_sequence(gt, x_bins=x_bins, y_bins=y_bins)

    return float(levenshtein_distance_from_sequences(pred_seq, gt_seq))


def _aoi_grid_position(
    aoi_id: int,
    x_bins: int,
) -> tuple[int, int]:
    """
    Convert AOI ID to grid coordinates.
    """
    y = aoi_id // x_bins
    x = aoi_id % x_bins

    return x, y


def _aoi_similarity(
    aoi_a: int,
    aoi_b: int,
    x_bins: int,
    y_bins: int,
    threshold: float = 3.5,
) -> float:
    """
    Spatial substitution similarity between two AOI cells.

    Similar cells receive a high score.
    Distant cells receive a low or negative score.

    This follows the idea of ScanMatch-style spatial substitution matrices.
    """
    ax, ay = _aoi_grid_position(aoi_a, x_bins=x_bins)
    bx, by = _aoi_grid_position(aoi_b, x_bins=x_bins)

    distance = float(np.sqrt((ax - bx) ** 2 + (ay - by) ** 2))

    if distance <= threshold:
        return 1.0 - (distance / threshold)

    return -0.5


def needleman_wunsch_similarity_from_sequences(
    seq_a: list[int],
    seq_b: list[int],
    x_bins: int = 12,
    y_bins: int = 8,
    gap_penalty: float = -0.1,
    threshold: float = 3.5,
) -> float:
    """
    Needleman-Wunsch global alignment similarity for AOI sequences.

    Higher is better.

    Output is clipped to [0, 1].
    """
    n = len(seq_a)
    m = len(seq_b)

    if n == 0 or m == 0:
        return np.nan

    dp = np.zeros((n + 1, m + 1), dtype=float)

    for i in range(1, n + 1):
        dp[i, 0] = dp[i - 1, 0] + gap_penalty

    for j in range(1, m + 1):
        dp[0, j] = dp[0, j - 1] + gap_penalty

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            substitution_score = _aoi_similarity(
                seq_a[i - 1],
                seq_b[j - 1],
                x_bins=x_bins,
                y_bins=y_bins,
                threshold=threshold,
            )

            dp[i, j] = max(
                dp[i - 1, j] + gap_penalty,
                dp[i, j - 1] + gap_penalty,
                dp[i - 1, j - 1] + substitution_score,
            )

    max_possible = float(min(n, m))

    if max_possible <= 0:
        return np.nan

    similarity = dp[n, m] / max_possible

    return float(np.clip(similarity, 0.0, 1.0))


def needleman_wunsch_similarity(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    x_bins: int = 12,
    y_bins: int = 8,
) -> float:
    """
    Needleman-Wunsch similarity between predicted and human AOI sequences.

    Higher is better.
    """
    pred_seq = scanpath_to_aoi_sequence(pred, x_bins=x_bins, y_bins=y_bins)
    gt_seq = scanpath_to_aoi_sequence(gt, x_bins=x_bins, y_bins=y_bins)

    return needleman_wunsch_similarity_from_sequences(
        pred_seq,
        gt_seq,
        x_bins=x_bins,
        y_bins=y_bins,
    )


def scanmatch_similarity(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    x_bins: int = 12,
    y_bins: int = 8,
    threshold: float = 3.5,
    gap_penalty: float = -0.1,
) -> float:
    """
    ScanMatch-style similarity.

    This implementation:
        1. converts scanpaths to AOI/grid sequences
        2. aligns the sequences using Needleman-Wunsch
        3. uses spatially informed substitution scores

    Higher is better.

    Note:
        This is a Python ScanMatch-style implementation, not the original
        MATLAB ScanMatch toolbox.
    """
    pred_seq = scanpath_to_aoi_sequence(pred, x_bins=x_bins, y_bins=y_bins)
    gt_seq = scanpath_to_aoi_sequence(gt, x_bins=x_bins, y_bins=y_bins)

    return needleman_wunsch_similarity_from_sequences(
        pred_seq,
        gt_seq,
        x_bins=x_bins,
        y_bins=y_bins,
        gap_penalty=gap_penalty,
        threshold=threshold,
    )


def aoi_transition_similarity(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    x_bins: int = 12,
    y_bins: int = 8,
) -> float:
    """
    Compare AOI transition patterns between two scanpaths.

    A transition is an ordered pair:
        AOI_i -> AOI_{i+1}

    The metric computes cosine similarity between transition-count vectors.

    Higher is better.
    """
    pred_seq = scanpath_to_aoi_sequence(pred, x_bins=x_bins, y_bins=y_bins)
    gt_seq = scanpath_to_aoi_sequence(gt, x_bins=x_bins, y_bins=y_bins)

    if len(pred_seq) < 2 or len(gt_seq) < 2:
        return np.nan

    pred_transitions = Counter(zip(pred_seq[:-1], pred_seq[1:]))
    gt_transitions = Counter(zip(gt_seq[:-1], gt_seq[1:]))

    all_keys = set(pred_transitions) | set(gt_transitions)

    if not all_keys:
        return np.nan

    pred_vec = np.array([pred_transitions.get(k, 0) for k in all_keys], dtype=float)
    gt_vec = np.array([gt_transitions.get(k, 0) for k in all_keys], dtype=float)

    denom = np.linalg.norm(pred_vec) * np.linalg.norm(gt_vec)

    if denom == 0:
        return np.nan

    return float(np.dot(pred_vec, gt_vec) / denom)


# ---------------------------------------------------------------------
# Spatial set-based metrics
# ---------------------------------------------------------------------


def eyenalysis_distance(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
) -> float:
    """
    Eyenalysis-style spatial distance.

    This compares the two scanpaths as sets of fixation points.

    It computes the average nearest-neighbor mismatch in both directions:

        predicted -> human
        human -> predicted

    Lower is better.

    Important:
        This metric ignores fixation order.
    """
    pred_xy = _to_xy(pred)
    gt_xy = _to_xy(gt)

    if len(pred_xy) == 0 or len(gt_xy) == 0:
        return np.nan

    distances = pairwise_distances(pred_xy, gt_xy)

    pred_to_gt = np.min(distances, axis=1).mean()
    gt_to_pred = np.min(distances, axis=0).mean()

    return float((pred_to_gt + gt_to_pred) / 2.0)


def _mannan_dissimilarity(
    a: np.ndarray,
    b: np.ndarray,
) -> float:
    """
    Mannan-style spatial dissimilarity for normalized coordinates.

    Lower means more spatially similar.
    """
    n = len(a)
    m = len(b)

    if n == 0 or m == 0:
        return np.nan

    distances = pairwise_distances(a, b)

    a_to_b = np.min(distances, axis=1)
    b_to_a = np.min(distances, axis=0)

    numerator = (m * np.sum(a_to_b**2)) + (n * np.sum(b_to_a**2))

    # For normalized coordinates, width=1 and height=1.
    # The diagonal term is width^2 + height^2 = 2.
    denominator = 2.0 * n * m * 2.0

    return float(numerator / denominator)


def mannan_similarity(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    n_random: int = 20,
    seed: int = 42,
) -> float:
    """
    Mannan-style normalized spatial similarity.

    The scanpath dissimilarity is compared against a random baseline.

    Higher is better.

    Output is clipped to [0, 1].

    Important:
        This metric ignores fixation order.

    Note:
        Despite the registry name `mannan_distance`, this function returns
        a similarity score, not a raw distance.
    """
    if n_random < 1:
        raise ValueError("n_random must be at least 1.")

    pred_xy = _to_xy(pred)
    gt_xy = _to_xy(gt)

    if len(pred_xy) == 0 or len(gt_xy) == 0:
        return np.nan

    observed = _mannan_dissimilarity(pred_xy, gt_xy)

    if np.isnan(observed):
        return np.nan

    rng = np.random.default_rng(seed)
    random_values = []

    for _ in range(n_random):
        random_pred = rng.random(size=pred_xy.shape)
        random_gt = rng.random(size=gt_xy.shape)
        random_values.append(_mannan_dissimilarity(random_pred, random_gt))

    baseline = float(np.nanmean(random_values))

    if baseline <= 0 or np.isnan(baseline):
        return np.nan

    similarity = 1.0 - (observed / baseline)

    return float(np.clip(similarity, 0.0, 1.0))


# ---------------------------------------------------------------------
# Recurrence-based metrics
# ---------------------------------------------------------------------


def cross_recurrence_matrix(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    threshold: float = 0.05,
) -> np.ndarray:
    """
    Compute a cross-recurrence matrix between two scanpaths.

    A cell is recurrent if the Euclidean distance between two fixations
    is smaller than the threshold.

    Coordinates are normalized to [0, 1].

    Args:
        threshold:
            Spatial recurrence threshold in normalized coordinates.
            Example: 0.05 means 5% of the normalized image scale.
    """
    pred_xy = _to_xy(pred)
    gt_xy = _to_xy(gt)

    if len(pred_xy) == 0 or len(gt_xy) == 0:
        return np.empty((len(pred_xy), len(gt_xy)), dtype=int)

    distances = pairwise_distances(pred_xy, gt_xy)

    return (distances < threshold).astype(int)


def _count_points_in_runs(
    values: np.ndarray,
    min_length: int = 2,
) -> int:
    """
    Count points that belong to runs of 1s with length >= min_length.
    """
    count = 0
    run_length = 0

    for value in values:
        if value == 1:
            run_length += 1
        else:
            if run_length >= min_length:
                count += run_length
            run_length = 0

    if run_length >= min_length:
        count += run_length

    return count


def recurrence_rate(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    threshold: float = 0.05,
) -> float:
    """
    Cross-recurrence rate.

    Percentage of recurrent fixation pairs.

    Descriptive metric.
    """
    matrix = cross_recurrence_matrix(pred, gt, threshold=threshold)

    if matrix.size == 0:
        return np.nan

    return float(100.0 * matrix.sum() / matrix.size)


def determinism(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    threshold: float = 0.05,
    min_line_length: int = 2,
) -> float:
    """
    Determinism of the cross-recurrence matrix.

    Measures the percentage of recurrent points that form diagonal lines.

    Diagonal lines indicate similar sequential structure.

    Descriptive metric.
    """
    matrix = cross_recurrence_matrix(pred, gt, threshold=threshold)

    recurrent_points = int(matrix.sum())

    if recurrent_points == 0:
        return np.nan

    n_rows, n_cols = matrix.shape

    diagonal_points = 0

    for offset in range(-n_rows + 1, n_cols):
        diagonal = np.diagonal(matrix, offset=offset)
        diagonal_points += _count_points_in_runs(
            diagonal,
            min_length=min_line_length,
        )

    return float(100.0 * diagonal_points / recurrent_points)


def laminarity(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    threshold: float = 0.05,
    min_line_length: int = 2,
) -> float:
    """
    Laminarity of the cross-recurrence matrix.

    Measures the percentage of recurrent points that form horizontal
    or vertical lines.

    Horizontal/vertical lines indicate repeated or stable states.

    Descriptive metric.
    """
    matrix = cross_recurrence_matrix(pred, gt, threshold=threshold)

    recurrent_points = int(matrix.sum())

    if recurrent_points == 0:
        return np.nan

    horizontal_points = 0
    vertical_points = 0

    for row in matrix:
        horizontal_points += _count_points_in_runs(
            row,
            min_length=min_line_length,
        )

    for col_idx in range(matrix.shape[1]):
        vertical_points += _count_points_in_runs(
            matrix[:, col_idx],
            min_length=min_line_length,
        )

    return float(
        100.0 * (horizontal_points + vertical_points) / (2.0 * recurrent_points)
    )


def corm(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    threshold: float = 0.05,
) -> float:
    """
    Center of recurrence mass.

    Measures the average temporal displacement of recurrent points
    away from the main diagonal.

    Smaller values mean recurrent points are closer to the same relative
    time index. Larger values mean recurrence occurs with stronger temporal
    displacement.

    Descriptive metric.
    """
    matrix = cross_recurrence_matrix(pred, gt, threshold=threshold)

    recurrent_points = int(matrix.sum())

    if recurrent_points == 0:
        return np.nan

    row_idx, col_idx = np.where(matrix == 1)

    n_rows, n_cols = matrix.shape

    if n_rows <= 1 or n_cols <= 1:
        return np.nan

    row_time = row_idx / (n_rows - 1)
    col_time = col_idx / (n_cols - 1)

    temporal_displacement = np.abs(row_time - col_time)

    return float(100.0 * np.mean(temporal_displacement))


# ---------------------------------------------------------------------
# Temporal embedding metrics
# ---------------------------------------------------------------------


def _time_delay_vectors(
    xy: np.ndarray,
    k: int = 3,
) -> np.ndarray:
    """
    Create time-delay embedding vectors from a fixation sequence.

    For k=3:

        [(x1, y1), (x2, y2), (x3, y3)]
        [(x2, y2), (x3, y3), (x4, y4)]
        ...

    Returns:
        Array with shape (n_vectors, k, 2).
    """
    if len(xy) < k:
        return np.empty((0, k, 2), dtype=float)

    vectors = []

    for i in range(0, len(xy) - k + 1):
        vectors.append(xy[i : i + k])

    return np.asarray(vectors, dtype=float)


def tde_distance(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    k: int = 3,
    mode: str = "mean",
) -> float:
    """
    Symmetric time-delay embedding distance.

    Each scanpath is converted into overlapping k-fixation subsequences.
    Each embedded vector has shape (k, 2).

    The distance between two embedded vectors is the mean Euclidean
    distance between corresponding fixations inside the k-length window.

    In mode="mean", the metric is bidirectional:
        predicted windows -> closest human windows
        human windows -> closest predicted windows

    The final score is the average of both directions.

    In mode="hausdorff", the metric returns the maximum nearest-neighbor
    embedded-vector distance across both directions.

    Lower is better.

    Args:
        pred:
            Predicted scanpath.
        gt:
            Ground-truth human scanpath.
        k:
            Embedding dimension, i.e. number of consecutive fixations.
        mode:
            "mean" or "hausdorff".

    Returns:
        TDE distance. Returns NaN if either scanpath has fewer than k fixations.
    """
    pred_xy = _to_xy(pred)
    gt_xy = _to_xy(gt)

    pred_vectors = _time_delay_vectors(pred_xy, k=k)
    gt_vectors = _time_delay_vectors(gt_xy, k=k)

    if len(pred_vectors) == 0 or len(gt_vectors) == 0:
        return np.nan

    # Pairwise distance between embedded vectors.
    # Each embedded-vector distance is the mean Euclidean distance
    # between corresponding points inside the k-length subsequence.
    diff = pred_vectors[:, None, :, :] - gt_vectors[None, :, :, :]
    point_distances = np.linalg.norm(diff, axis=3)
    vector_distances = point_distances.mean(axis=2)

    pred_to_gt = np.min(vector_distances, axis=1)
    gt_to_pred = np.min(vector_distances, axis=0)

    if mode == "mean":
        return float((pred_to_gt.mean() + gt_to_pred.mean()) / 2.0)

    if mode == "hausdorff":
        return float(max(pred_to_gt.max(), gt_to_pred.max()))

    raise ValueError("mode must be either 'mean' or 'hausdorff'.")


def scaled_tde_distance(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    k: int = 3,
    mode: str = "mean",
) -> float:
    """
    Scaled time-delay embedding distance.

    This is TDE normalized by the maximum possible distance between two
    normalized fixation points, sqrt(2).

    Lower is better.

    Output is approximately in [0, 1].
    """
    distance = tde_distance(pred, gt, k=k, mode=mode)

    if np.isnan(distance):
        return np.nan

    return float(distance / np.sqrt(2.0))


def sequence_score(
    pred: pd.DataFrame,
    gt: pd.DataFrame,
    x_bins: int = 12,
    y_bins: int = 8,
) -> float:
    """
    Sequence Score between predicted and human AOI sequences.

    This is a normalized sequence similarity based on Levenshtein distance.

    Steps:
        1. Convert both scanpaths to AOI/grid sequences.
        2. Compute Levenshtein edit distance.
        3. Normalize by the longer sequence length.
        4. Convert distance to similarity.

    Score:
        1.0 = identical AOI sequences
        0.0 = maximally different under this normalization

    Higher is better.
    """
    pred_seq = scanpath_to_aoi_sequence(pred, x_bins=x_bins, y_bins=y_bins)
    gt_seq = scanpath_to_aoi_sequence(gt, x_bins=x_bins, y_bins=y_bins)

    max_len = max(len(pred_seq), len(gt_seq))

    if max_len == 0:
        return np.nan

    distance = levenshtein_distance_from_sequences(pred_seq, gt_seq)

    score = 1.0 - (distance / max_len)

    return float(np.clip(score, 0.0, 1.0))


def number_of_fixations(
    pred: pd.DataFrame,
    gt: pd.DataFrame | None = None,
) -> float:
    """
    Number of fixations in the predicted scanpath.

    This is a descriptive scanpath statistic, not a comparison metric.

    The `gt` argument is accepted only to keep the same metric function
    signature as the other scanpath metrics.

    Descriptive metric.
    """
    xy = _to_xy(pred)

    return float(len(xy))


def aoi_transition_count(
    pred: pd.DataFrame,
    gt: pd.DataFrame | None = None,
    x_bins: int = 12,
    y_bins: int = 8,
    count_self_transitions: bool = False,
) -> float:
    """
    Count the number of AOI transitions in the predicted scanpath.

    A transition is counted when the scanpath moves from one AOI/grid cell
    to another consecutive AOI/grid cell.

    Args:
        count_self_transitions:
            If False, transitions such as A -> A are ignored.
            If True, all consecutive AOI pairs are counted.

    This is a descriptive scanpath statistic, not a comparison metric.

    Descriptive metric.
    """
    seq = scanpath_to_aoi_sequence(pred, x_bins=x_bins, y_bins=y_bins)

    if len(seq) < 2:
        return 0.0

    count = 0

    for current_aoi, next_aoi in zip(seq[:-1], seq[1:]):
        if count_self_transitions or current_aoi != next_aoi:
            count += 1

    return float(count)


SCANPATH_METRICS = {
    "mean_fixation_error": ScanpathMetric(
        name="mean_fixation_error",
        function=mean_fixation_error,
        category="pointwise",
        direction="lower",
        description=(
            "Mean Euclidean distance between corresponding predicted "
            "and human fixations."
        ),
    ),
    "final_fixation_error": ScanpathMetric(
        name="final_fixation_error",
        function=final_fixation_error,
        category="pointwise",
        direction="lower",
        description=(
            "Euclidean distance between the final predicted fixation "
            "and the final human fixation."
        ),
    ),
    "mean_saccade_amplitude_error": ScanpathMetric(
        name="mean_saccade_amplitude_error",
        function=mean_saccade_amplitude_error,
        category="pointwise",
        direction="lower",
        description=(
            "Mean absolute error between predicted and human saccade amplitudes."
        ),
    ),
    "mean_saccade_angle_error": ScanpathMetric(
        name="mean_saccade_angle_error",
        function=mean_saccade_angle_error,
        category="pointwise",
        direction="lower",
        description=(
            "Mean angular difference between predicted and human saccade "
            "directions in radians."
        ),
    ),
    "mean_duration_error": ScanpathMetric(
        name="mean_duration_error",
        function=mean_duration_error,
        category="temporal",
        direction="lower",
        description=(
            "Mean absolute error between predicted and human fixation durations."
        ),
        requires_duration=True,
    ),
    "duration_correlation": ScanpathMetric(
        name="duration_correlation",
        function=duration_correlation,
        category="temporal",
        direction="higher",
        description=(
            "Pearson correlation between predicted and human fixation durations."
        ),
        requires_duration=True,
    ),
    "dtw": ScanpathMetric(
        name="dtw",
        function=dtw_distance,
        category="alignment",
        direction="lower",
        description=(
            "Dynamic Time Warping distance between predicted and human "
            "fixation coordinate sequences."
        ),
    ),
    "frechet": ScanpathMetric(
        name="frechet",
        function=discrete_frechet_distance,
        category="alignment",
        direction="lower",
        description=(
            "Discrete Fréchet distance between predicted and human ordered "
            "fixation paths."
        ),
    ),
    "hausdorff": ScanpathMetric(
        name="hausdorff",
        function=hausdorff_distance,
        category="alignment",
        direction="lower",
        description=(
            "Symmetric Hausdorff distance between predicted and human fixation "
            "point sets. This metric ignores fixation order."
        ),
    ),
    "multimatch_shape": ScanpathMetric(
        name="multimatch_shape",
        function=multimatch_shape,
        category="multimatch",
        direction="higher",
        description="MultiMatch shape/vector similarity using the multimatch-gaze implementation.",
    ),
    "multimatch_direction": ScanpathMetric(
        name="multimatch_direction",
        function=multimatch_direction,
        category="multimatch",
        direction="higher",
        description="MultiMatch direction similarity using the multimatch-gaze implementation.",
    ),
    "multimatch_length": ScanpathMetric(
        name="multimatch_length",
        function=multimatch_length,
        category="multimatch",
        direction="higher",
        description="MultiMatch length similarity using the multimatch-gaze implementation.",
    ),
    "multimatch_position": ScanpathMetric(
        name="multimatch_position",
        function=multimatch_position,
        category="multimatch",
        direction="higher",
        description="MultiMatch position similarity using the multimatch-gaze implementation.",
    ),
    "multimatch_duration": ScanpathMetric(
        name="multimatch_duration",
        function=multimatch_duration,
        category="multimatch",
        direction="higher",
        description="MultiMatch duration similarity using the multimatch-gaze implementation.",
        requires_duration=True,
    ),
    # ---------------------------------------------------------------------
    # Symbolic / AOI metrics
    # ---------------------------------------------------------------------
    "scanmatch": ScanpathMetric(
        name="scanmatch",
        function=scanmatch_similarity,
        category="symbolic",
        direction="higher",
        description=(
            "ScanMatch-style AOI sequence alignment similarity using a "
            "spatial substitution matrix."
        ),
    ),
    "levenshtein": ScanpathMetric(
        name="levenshtein",
        function=levenshtein_distance_metric,
        category="symbolic",
        direction="lower",
        description=(
            "Levenshtein edit distance between predicted and human AOI sequences."
        ),
    ),
    "needleman_wunsch": ScanpathMetric(
        name="needleman_wunsch",
        function=needleman_wunsch_similarity,
        category="symbolic",
        direction="higher",
        description=(
            "Needleman-Wunsch global alignment similarity between AOI sequences."
        ),
    ),
    "aoi_transition_similarity": ScanpathMetric(
        name="aoi_transition_similarity",
        function=aoi_transition_similarity,
        category="symbolic",
        direction="higher",
        description=(
            "Cosine similarity between predicted and human AOI transition-count vectors."
        ),
    ),
    # ---------------------------------------------------------------------
    # Spatial set-based metrics
    # ---------------------------------------------------------------------
    "eyenalysis": ScanpathMetric(
        name="eyenalysis",
        function=eyenalysis_distance,
        category="spatial",
        direction="lower",
        description=(
            "Symmetric nearest-neighbor spatial distance between fixation sets. "
            "This metric ignores fixation order."
        ),
    ),
    "mannan_distance": ScanpathMetric(
        name="mannan_distance",
        function=mannan_similarity,
        category="spatial",
        direction="higher",
        description=(
            "Mannan-style spatial similarity normalized by a random baseline. "
            "This metric ignores fixation order."
        ),
    ),
    # ---------------------------------------------------------------------
    # Recurrence metrics
    # ---------------------------------------------------------------------
    "recurrence": ScanpathMetric(
        name="recurrence",
        function=recurrence_rate,
        category="recurrence",
        direction="descriptive",
        description=(
            "Cross-recurrence rate: percentage of fixation pairs closer than "
            "a spatial threshold."
        ),
    ),
    "determinism": ScanpathMetric(
        name="determinism",
        function=determinism,
        category="recurrence",
        direction="descriptive",
        description=(
            "Percentage of recurrent points forming diagonal lines in the "
            "cross-recurrence matrix."
        ),
    ),
    "laminarity": ScanpathMetric(
        name="laminarity",
        function=laminarity,
        category="recurrence",
        direction="descriptive",
        description=(
            "Percentage of recurrent points forming horizontal or vertical lines "
            "in the cross-recurrence matrix."
        ),
    ),
    "corm": ScanpathMetric(
        name="corm",
        function=corm,
        category="recurrence",
        direction="descriptive",
        description=(
            "Center of recurrence mass: average temporal displacement of recurrent "
            "points from the main diagonal."
        ),
    ),
    # ---------------------------------------------------------------------
    # Temporal embedding metrics
    # ---------------------------------------------------------------------
    "tde": ScanpathMetric(
        name="tde",
        function=tde_distance,
        category="temporal-embedding",
        direction="lower",
        description=(
            "Time-delay embedding distance between local k-fixation subsequences."
        ),
    ),
    "scaled_tde": ScanpathMetric(
        name="scaled_tde",
        function=scaled_tde_distance,
        category="temporal-embedding",
        direction="lower",
        description=("Scaled time-delay embedding distance normalized by sqrt(2)."),
    ),
    "sequence_score": ScanpathMetric(
        name="sequence_score",
        function=sequence_score,
        category="symbolic",
        direction="higher",
        description=(
            "Normalized AOI sequence similarity based on Levenshtein distance. "
            "Higher values indicate more similar AOI sequences."
        ),
    ),
    "number_of_fixations": ScanpathMetric(
        name="number_of_fixations",
        function=number_of_fixations,
        category="scanpath-statistic",
        direction="descriptive",
        description=(
            "Number of fixations in the predicted scanpath. "
            "This is a descriptive statistic, not a prediction-vs-human comparison metric."
        ),
    ),
    "aoi_transition_count": ScanpathMetric(
        name="aoi_transition_count",
        function=aoi_transition_count,
        category="scanpath-statistic",
        direction="descriptive",
        description=(
            "Number of transitions between AOI/grid cells in the predicted scanpath. "
            "Self-transitions are ignored by default."
        ),
    ),
}
