# Scanpath Metrics

This document describes the scanpath metrics used in the benchmark for comparing predicted scanpaths with human scanpaths.

Scanpath comparison is not one-dimensional. Two scanpaths can be similar in fixation locations but different in order, similar in order but different in timing, or similar in spatial coverage but different in saccade direction.

For this reason, the benchmark uses multiple metric families:

- point-wise geometric metrics
- temporal metrics
- alignment-based metrics
- MultiMatch metrics
- symbolic / grid-AOI metrics
- spatial set-based metrics
- recurrence-based metrics
- temporal-embedding metrics
- descriptive scanpath statistics

The goal is not to rely on one single metric, but to evaluate scanpath predictions from multiple perspectives. Each metric is documented with its definition, interpretation, expected range, direction, and relevant references.

---

## Expected Scanpath Format

All scanpath metrics assume that both predicted and ground-truth scanpaths are stored as tabular data.

Ground-truth human scanpaths should use the following columns:

```text
image_id, subject_id, fixation_index, x, y, duration
```

Predicted scanpaths should use the following columns:

```text
image_id, prediction_id, model, sampler, fixation_index, x, y, duration
```

For predicted scanpaths, `prediction_id` identifies one generated scanpath. For example, it can represent a model sample, a random seed, or a human subject treated as a pseudo-prediction in human group-vs-human group evaluation.

### Coordinate convention

The fixation coordinates should be normalized:

```text
x in [0, 1]
y in [0, 1]
```

This means that all spatial errors are reported in normalized image coordinates, not in pixels.

For example, if the image width is 1000 pixels, an x-error of `0.10` corresponds to about 100 pixels horizontally.

A value of `0.0` means no spatial error.

The maximum possible normalized distance is:

```text
sqrt(2) ≈ 1.414
```

This occurs when one fixation is at one image corner, for example `(0, 0)`, and the other is at the opposite corner, for example `(1, 1)`.

### Duration convention

Fixation duration should be reported in milliseconds.

If duration is unavailable, use:

```text
duration = -1
```

Duration-based metrics ignore invalid durations.

---

## Metric Categories

The current implementation includes the following metric categories:

```text
pointwise
temporal
alignment
multimatch
symbolic
spatial
recurrence
temporal-embedding
scanpath-statistic
```

### Point-wise geometric metrics

Point-wise geometric metrics compare fixation locations, saccade amplitudes, and saccade directions at corresponding fixation or saccade indices.

Implemented metrics:

```text
mean_fixation_error
final_fixation_error
mean_saccade_amplitude_error
mean_saccade_angle_error
```

### Temporal metrics

Temporal metrics compare fixation durations.

Implemented metrics:

```text
mean_duration_error
duration_correlation
```

### Alignment metrics

Alignment metrics compare scanpath sequences while allowing some flexibility in timing or sequence length.

Implemented metrics:

```text
dtw
frechet
hausdorff
```

### MultiMatch metrics

MultiMatch compares scanpaths across multiple dimensions: shape, direction, length, position, and duration.

Implemented metrics:

```text
multimatch_shape
multimatch_direction
multimatch_length
multimatch_position
multimatch_duration
```

### Symbolic / grid-AOI metrics

Symbolic metrics convert fixation coordinates into grid-based AOI sequences and compare those sequences.

Implemented metrics:

```text
scanmatch
levenshtein
needleman_wunsch
aoi_transition_similarity
sequence_score
```

### Scanpath statistics

Scanpath statistics describe properties of generated scanpaths rather than directly measuring prediction-vs-human similarity.

Implemented metrics:

```text
number_of_fixations
aoi_transition_count
```

### Spatial set-based metrics

Spatial set-based metrics compare fixation sets while mostly ignoring fixation order.

Implemented metrics:

```text
eyenalysis
mannan_distance
```

### Recurrence-based metrics

Recurrence metrics analyze repeated spatial states using a cross-recurrence matrix.

Implemented metrics:

```text
recurrence
determinism
laminarity
corm
```

### Temporal-embedding metrics

Temporal-embedding metrics compare local subsequences of scanpaths.

Implemented metrics:

```text
tde
scaled_tde
```

---

## Metrics Summary

| Metric | Category | Direction | Requires duration | Range | If prediction and human scanpath are exactly the same |
|---|---|---|---|---|---|
| `mean_fixation_error` | pointwise | lower | no | `[0, sqrt(2)]` | `0.0` |
| `final_fixation_error` | pointwise | lower | no | `[0, sqrt(2)]` | `0.0` |
| `mean_saccade_amplitude_error` | pointwise | lower | no | `[0, sqrt(2)]` | `0.0` |
| `mean_saccade_angle_error` | pointwise | lower | no | `[0, pi]` radians | `0.0` |
| `mean_duration_error` | temporal | lower | yes | `[0, +inf)` ms | `0.0` |
| `duration_correlation` | temporal | higher | yes | `[-1, 1]` or `NaN` | `1.0`, if durations have non-zero variance; otherwise `NaN` |
| `dtw` | alignment | lower | no | `[0, +inf)`; usually small with normalized coordinates | `0.0` |
| `frechet` | alignment | lower | no | `[0, sqrt(2)]` | `0.0` |
| `hausdorff` | alignment | lower | no | `[0, sqrt(2)]` | `0.0` |
| `multimatch_shape` | multimatch | higher | no | `[0, 1]` | `1.0` |
| `multimatch_direction` | multimatch | higher | no | `[0, 1]` | `1.0` |
| `multimatch_length` | multimatch | higher | no | `[0, 1]` | `1.0` |
| `multimatch_position` | multimatch | higher | no | `[0, 1]` | `1.0` |
| `multimatch_duration` | multimatch | higher | yes | `[0, 1]` or `NaN` | `1.0`, if valid durations are available |
| `scanmatch` | symbolic | higher | no | usually `[0, 1]` in this implementation | `1.0` |
| `levenshtein` | symbolic | lower | no | `[0, max(len(pred), len(gt))]` | `0.0` |
| `needleman_wunsch` | symbolic | higher | no | usually `[0, 1]` in this implementation | `1.0` |
| `aoi_transition_similarity` | symbolic | higher | no | `[0, 1]` or `NaN` | `1.0`, if at least one transition exists |
| `sequence_score` | symbolic | higher | no | `[0, 1]` | `1.0` |
| `number_of_fixations` | scanpath-statistic | descriptive | no | non-negative integer | Number of fixations in the predicted scanpath, so `N` |
| `aoi_transition_count` | scanpath-statistic | descriptive | no | integer in `[0, N - 1]` | Number of grid-AOI changes in the predicted scanpath |
| `eyenalysis` | spatial | lower | no | `[0, sqrt(2)]` | `0.0` |
| `mannan_distance` | spatial | higher | no | `[0, 1]` in this implementation | `1.0` |
| `recurrence` | recurrence | descriptive | no | `[0, 100]` | Depends on threshold and scanpath length; with only diagonal matches, `100 / N` for `N` fixations |
| `determinism` | recurrence | descriptive | no | `[0, 100]` or `NaN` | Usually `100.0` if recurrent points form a diagonal line |
| `laminarity` | recurrence | descriptive | no | `[0, 100]` or `NaN` | Often `0.0` for simple one-to-one diagonal matches |
| `corm` | recurrence | descriptive | no | `[0, 100]` or `NaN` | `0.0` if recurrent points lie on the main diagonal |
| `tde` | temporal-embedding | lower | no | approximately `[0, sqrt(2)]` | `0.0` |
| `scaled_tde` | temporal-embedding | lower | no | approximately `[0, 1]` | `0.0` |

---

## Short Metric Definitions

| Metric | Short definition |
|---|---|
| `mean_fixation_error` | Average spatial distance between predicted and human fixations at the same fixation index. |
| `final_fixation_error` | Spatial distance between the final predicted fixation and the final human fixation. |
| `mean_saccade_amplitude_error` | Average difference between predicted and human saccade lengths. |
| `mean_saccade_angle_error` | Average angular difference between predicted and human saccade directions. |
| `mean_duration_error` | Average absolute difference between predicted and human fixation durations. |
| `duration_correlation` | Pearson correlation between predicted and human fixation-duration sequences. |
| `dtw` | Flexible sequence-alignment distance between scanpaths. |
| `frechet` | Ordered path distance that captures the largest mismatch along the best traversal. |
| `hausdorff` | Spatial set distance measuring the largest nearest-neighbor mismatch; ignores order. |
| `multimatch_shape` | MultiMatch component comparing the overall saccade-vector shape. |
| `multimatch_direction` | MultiMatch component comparing saccade directions. |
| `multimatch_length` | MultiMatch component comparing saccade amplitudes. |
| `multimatch_position` | MultiMatch component comparing fixation positions. |
| `multimatch_duration` | MultiMatch component comparing fixation durations. |
| `scanmatch` | Symbolic sequence-alignment similarity after converting fixations into grid-AOI labels. |
| `levenshtein` | Edit distance between two grid-AOI sequences. |
| `needleman_wunsch` | Global sequence-alignment similarity between two grid-AOI sequences. |
| `aoi_transition_similarity` | Similarity between predicted and human grid-AOI transition patterns. |
| `sequence_score` | Normalized grid-AOI sequence similarity based on Levenshtein distance. |
| `number_of_fixations` | Number of fixations in the predicted scanpath. |
| `aoi_transition_count` | Number of times the predicted scanpath moves from one grid AOI to another. |
| `eyenalysis` | Symmetric nearest-neighbor spatial distance between two fixation sets; ignores order. |
| `mannan_distance` | Spatial similarity comparing observed fixation-set mismatch against a random baseline. |
| `recurrence` | Percentage of fixation pairs that are spatially close in the cross-recurrence matrix. |
| `determinism` | Percentage of recurrent points forming diagonal lines. |
| `laminarity` | Percentage of recurrent points forming horizontal or vertical lines. |
| `corm` | Average temporal displacement of recurrent points from the main diagonal. |
| `tde` | Distance between local k-fixation subsequences using time-delay embedding. |
| `scaled_tde` | TDE normalized by the maximum possible normalized spatial distance. |

---

## Detailed Metric Definitions

This section documents each metric family in detail. Each metric includes its metric name, category, direction, range, definition, formula, interpretation, and limitations.

---

## Point-wise Geometric Metrics

Point-wise geometric metrics compare predicted and human scanpaths using fixation coordinates and saccade geometry.

These metrics assume that the predicted and human scanpaths are aligned by fixation index. For example, fixation 1 is compared with fixation 1, fixation 2 with fixation 2, and so on.

If two scanpaths have different lengths, the current implementation truncates both scanpaths to the shorter length.

Notation used in this section:

```text
p = predicted scanpath
g = ground-truth / human scanpath
i = fixation index
n = number of compared fixations
```

### 1. Mean Fixation Error

#### Metric name

```text
mean_fixation_error
```

#### Category

```text
pointwise
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, \sqrt{2}]
$$

#### Definition

Mean Fixation Error measures the average Euclidean distance between corresponding predicted and human fixations.

It compares fixation points with the same fixation index:

```text
predicted fixation 1  vs  human fixation 1
predicted fixation 2  vs  human fixation 2
predicted fixation 3  vs  human fixation 3
...
```

#### Formula

Let the predicted scanpath be:

$$
P =
\left[
(x^{p}_{1}, y^{p}_{1}),
\ldots,
(x^{p}_{n}, y^{p}_{n})
\right]
$$

and the human scanpath be:

$$
G =
\left[
(x^{g}_{1}, y^{g}_{1}),
\ldots,
(x^{g}_{n}, y^{g}_{n})
\right]
$$

Then Mean Fixation Error is:

$$
\mathrm{MFE}
=
\frac{1}{n}
\sum_{i=1}^{n}
\sqrt{
(x^{p}_{i} - x^{g}_{i})^{2}
+
(y^{p}_{i} - y^{g}_{i})^{2}
}
$$

#### Interpretation

- `0.0` means perfect fixation-position match.
- Higher values mean worse spatial agreement.

Because coordinates are normalized to `[0, 1]`, the metric is independent of the original image resolution.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{MFE} = 0
$$

#### Limitation

This metric assumes direct index-wise correspondence between scanpaths. It does not handle temporal shifts or local reordering well. For that reason, it should be complemented with alignment-based metrics such as DTW, Fréchet distance, MultiMatch, or ScanMatch.

---

### 2. Final Fixation Error

#### Metric name

```text
final_fixation_error
```

#### Category

```text
pointwise
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, \sqrt{2}]
$$

#### Definition

Final Fixation Error measures the Euclidean distance between the last predicted fixation and the last human fixation.

#### Formula

Let the final predicted fixation be:

$$
f^{p}_{n} = (x^{p}_{n}, y^{p}_{n})
$$

and the final human fixation be:

$$
f^{g}_{n} = (x^{g}_{n}, y^{g}_{n})
$$

Then Final Fixation Error is:

$$
\mathrm{FFE}
=
\sqrt{
(x^{p}_{n} - x^{g}_{n})^{2}
+
(y^{p}_{n} - y^{g}_{n})^{2}
}
$$

#### Interpretation

- `0.0` means the predicted scanpath ends at the same location as the human scanpath.
- Higher values mean worse final-location agreement.

#### Why this metric is useful

This metric checks whether the predicted scanpath eventually reaches a similar final region as the human scanpath.

This can be useful when later fixations are important, for example when evaluating whether a model eventually reaches a relevant object, region, or interface element.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{FFE} = 0
$$

#### Limitation

This metric only evaluates the endpoint of the scanpath. It ignores the full trajectory before the final fixation.

---

### 3. Mean Saccade Amplitude Error

#### Metric name

```text
mean_saccade_amplitude_error
```

#### Category

```text
pointwise
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, \sqrt{2}]
$$

#### Definition

A saccade is the movement between two consecutive fixations.

For example:

```text
fixation 1 -> fixation 2
fixation 2 -> fixation 3
fixation 3 -> fixation 4
```

Mean Saccade Amplitude Error compares the lengths of predicted saccades with the lengths of human saccades.

#### Formula

Let a predicted fixation be:

$$
f^{p}_{i} = (x^{p}_{i}, y^{p}_{i})
$$

and a human fixation be:

$$
f^{g}_{i} = (x^{g}_{i}, y^{g}_{i})
$$

The predicted saccade amplitude between fixation \(i\) and fixation \(i+1\) is:

$$
a^{p}_{i}
=
\left\|
f^{p}_{i+1} - f^{p}_{i}
\right\|
=
\sqrt{
(x^{p}_{i+1} - x^{p}_{i})^{2}
+
(y^{p}_{i+1} - y^{p}_{i})^{2}
}
$$

The human saccade amplitude is:

$$
a^{g}_{i}
=
\left\|
f^{g}_{i+1} - f^{g}_{i}
\right\|
=
\sqrt{
(x^{g}_{i+1} - x^{g}_{i})^{2}
+
(y^{g}_{i+1} - y^{g}_{i})^{2}
}
$$

Then Mean Saccade Amplitude Error is:

$$
\mathrm{MSAE}
=
\frac{1}{n - 1}
\sum_{i=1}^{n-1}
\left|
a^{p}_{i} - a^{g}_{i}
\right|
$$

#### Interpretation

- `0.0` means predicted saccade lengths match human saccade lengths.
- Higher values mean larger difference in movement amplitude.

#### Why this metric is useful

A predicted scanpath may visit similar regions but with unrealistic movement lengths.

For example, a human scanpath may use short local movements, while a model may jump across the image. This metric captures that difference.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{MSAE} = 0
$$

#### Limitation

This metric compares only the length of the movements. It does not compare their direction. For direction, use `mean_saccade_angle_error`.

---

### 4. Mean Saccade Angle Error

#### Metric name

```text
mean_saccade_angle_error
```

#### Category

```text
pointwise
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, \pi]
$$

The value is reported in radians.

#### Definition

Mean Saccade Angle Error compares the direction of predicted saccades with the direction of human saccades.

#### Formula

The direction of the predicted saccade from fixation \(i\) to fixation \(i+1\) is:

$$
\theta^{p}_{i}
=
\operatorname{atan2}
\left(
y^{p}_{i+1} - y^{p}_{i},
x^{p}_{i+1} - x^{p}_{i}
\right)
$$

The direction of the human saccade is:

$$
\theta^{g}_{i}
=
\operatorname{atan2}
\left(
y^{g}_{i+1} - y^{g}_{i},
x^{g}_{i+1} - x^{g}_{i}
\right)
$$

The angular difference is the smallest absolute difference between the two angles:

$$
\Delta \theta_i
=
\min
\left(
\left| \theta^{p}_{i} - \theta^{g}_{i} \right|,
2\pi - \left| \theta^{p}_{i} - \theta^{g}_{i} \right|
\right)
$$

Then Mean Saccade Angle Error is:

$$
\mathrm{MSAngE}
=
\frac{1}{n - 1}
\sum_{i=1}^{n-1}
\Delta \theta_i
$$

#### Interpretation

- `0` means same direction.
- `pi / 2` means 90 degrees difference.
- `pi` means opposite direction.
- Lower values mean better direction agreement.

#### Why this metric is useful

This metric checks whether the predicted scanpath follows a similar movement direction to the human scanpath.

It is related to the direction component of MultiMatch, but it is simpler and directly computed from corresponding saccades.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{MSAngE} = 0
$$

#### Limitation

This metric assumes direct index-wise correspondence between predicted and human saccades. It should be complemented with MultiMatch or alignment-based metrics.

---

## Temporal Metrics

Temporal metrics compare fixation durations between predicted and human scanpaths.

They require valid duration values. In this benchmark, fixation duration is expected to be reported in milliseconds.

If duration is unavailable, it should be encoded as:

```text
duration = -1
```

Invalid duration values are ignored by duration-based metrics.

### 5. Mean Duration Error

#### Metric name

```text
mean_duration_error
```

#### Category

```text
temporal
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, +\infty)
$$

The value is reported in milliseconds.

#### Definition

Mean Duration Error measures the average absolute difference between predicted and human fixation durations.

It compares fixation durations at the same fixation index.

#### Formula

Let the predicted duration sequence be:

$$
D^{p}
=
\left[
d^{p}_{1},
d^{p}_{2},
\ldots,
d^{p}_{n}
\right]
$$

and the human duration sequence be:

$$
D^{g}
=
\left[
d^{g}_{1},
d^{g}_{2},
\ldots,
d^{g}_{n}
\right]
$$

where \(d^{p}_{i}\) and \(d^{g}_{i}\) are fixation durations in milliseconds.

Then Mean Duration Error is:

$$
\mathrm{MDE}
=
\frac{1}{n}
\sum_{i=1}^{n}
\left|
d^{p}_{i} - d^{g}_{i}
\right|
$$

If some duration values are invalid, those pairs are ignored:

$$
d_i < 0
\Rightarrow
\text{invalid duration}
$$

#### Interpretation

- `0 ms` means predicted fixation durations match human fixation durations exactly.
- Higher values mean larger duration error.

For example, if:

$$
\mathrm{MDE} = 20
$$

then the predicted fixation durations differ from the human fixation durations by 20 ms on average.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{MDE} = 0
$$

#### Limitation

This metric should only be used when predicted durations are meaningful.

For example, if a sampler assigns the same fixed duration to every predicted fixation, this metric may be less informative. In that case, it can still show duration mismatch, but it does not tell whether the model learned realistic fixation timing.

---

### 6. Duration Correlation

#### Metric name

```text
duration_correlation
```

#### Category

```text
temporal
```

#### Direction

```text
higher is better
```

#### Range

$$
[-1, 1]
$$

The metric may return `NaN` when the correlation is undefined.

#### Definition

Duration Correlation measures whether predicted fixation durations vary similarly to human fixation durations.

Unlike Mean Duration Error, which measures the average absolute difference in milliseconds, Duration Correlation measures the similarity of the duration pattern.

For example, it checks whether long predicted fixations correspond to long human fixations, and short predicted fixations correspond to short human fixations.

#### Formula

Let the predicted duration sequence be:

$$
D^{p}
=
\left[
d^{p}_{1},
d^{p}_{2},
\ldots,
d^{p}_{n}
\right]
$$

and the human duration sequence be:

$$
D^{g}
=
\left[
d^{g}_{1},
d^{g}_{2},
\ldots,
d^{g}_{n}
\right]
$$

where \(d^{p}_{i}\) and \(d^{g}_{i}\) are fixation durations in milliseconds.

Duration Correlation is computed using Pearson correlation:

$$
r
=
\frac{
\sum_{i=1}^{n}
(d^{p}_{i} - \bar{d}^{p})
(d^{g}_{i} - \bar{d}^{g})
}
{
\sqrt{
\sum_{i=1}^{n}
(d^{p}_{i} - \bar{d}^{p})^{2}
}
\sqrt{
\sum_{i=1}^{n}
(d^{g}_{i} - \bar{d}^{g})^{2}
}
}
$$

where:

$$
\bar{d}^{p}
=
\frac{1}{n}
\sum_{i=1}^{n}
d^{p}_{i}
$$

and:

$$
\bar{d}^{g}
=
\frac{1}{n}
\sum_{i=1}^{n}
d^{g}_{i}
$$

Invalid duration pairs are ignored:

$$
d_i < 0
\Rightarrow
\text{invalid duration}
$$

#### Interpretation

- `1.0` means predicted and human durations vary in the same pattern.
- `0.0` means no linear relationship between predicted and human durations.
- `-1.0` means predicted and human durations vary in opposite patterns.

For example, a value close to `1.0` means that fixations that are long in the human scanpath are also long in the predicted scanpath.

#### If prediction and human scanpath are exactly the same

If the duration sequence has non-zero variance:

$$
r = 1
$$

If all durations are constant, the correlation is undefined and the metric returns:

```text
NaN
```

#### Invalid cases

The metric returns `NaN` if:

```text
fewer than 2 valid duration pairs are available
one of the duration sequences has zero variance
duration values are missing or invalid
```

#### Limitation

Duration Correlation does not measure the absolute size of the duration error.

For example, these two duration sequences have perfect correlation:

```text
human:      [100, 200, 300]
predicted:  [200, 400, 600]
```

but the predicted durations are still numerically too large.

Therefore, Duration Correlation should be interpreted together with `mean_duration_error`.

---

## Alignment Metrics

Alignment metrics compare the overall scanpath sequence while allowing more flexibility than point-wise metrics.

Point-wise metrics compare fixation 1 with fixation 1, fixation 2 with fixation 2, and so on. Alignment metrics are useful when two scanpaths visit similar regions but have different numbers of fixations, repeated fixations, or small temporal shifts.

The current implementation includes:

```text
dtw
frechet
hausdorff
```

### 7. Dynamic Time Warping Distance

#### Metric name

```text
dtw
```

#### Category

```text
alignment
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, +\infty)
$$

With normalized coordinates, values are usually small, but the accumulated DTW cost can exceed \(\sqrt{2}\) depending on scanpath length and alignment path.

#### Definition

Dynamic Time Warping, or DTW, measures the distance between two fixation sequences while allowing flexible alignment between them.

Unlike point-wise metrics, DTW does not require fixation \(i\) in the predicted scanpath to be compared only with fixation \(i\) in the human scanpath. Instead, it finds a low-cost alignment path between the two sequences.

This is useful when two scanpaths visit similar regions in a similar order but have different numbers of fixations or slightly different temporal pacing.

#### Intuition

For example:

```text
Human:     A -> B -> C -> D
Predicted: A -> B -> B -> C -> D
```

A strict point-wise metric may punish this strongly because the repeated `B` shifts the later fixation indices.

DTW can align the repeated `B` with the human `B`, then continue aligning the remaining sequence.

#### Formula

Let the predicted scanpath be:

$$
P = [p_1, p_2, \ldots, p_n]
$$

and the human scanpath be:

$$
G = [g_1, g_2, \ldots, g_m]
$$

where each fixation is a 2D point:

$$
p_i = (x^p_i, y^p_i)
$$

and:

$$
g_j = (x^g_j, y^g_j)
$$

The local cost between two fixations is the Euclidean distance:

$$
c(i,j) = \lVert p_i - g_j \rVert_2
$$

DTW computes a cumulative cost matrix:

$$
D(i,j)
=
c(i,j)
+
\min
\left(
D(i-1,j),
D(i,j-1),
D(i-1,j-1)
\right)
$$

The final normalized DTW distance used in this implementation is:

$$
\mathrm{DTW}
=
\frac{D(n,m)}{n + m}
$$

#### Interpretation

- `0.0` means identical or perfectly aligned scanpaths.
- Higher values mean worse sequence alignment.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{DTW} = 0
$$

#### Limitation

DTW is flexible, but this flexibility can also hide some differences. It may align repeated or stretched parts of a scanpath even when the temporal structure is not truly the same.

For this reason, DTW should be reported together with other metrics such as MultiMatch, ScanMatch, Fréchet distance, and point-wise geometric metrics.

---

### 8. Discrete Fréchet Distance

#### Metric name

```text
frechet
```

#### Category

```text
alignment
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, \sqrt{2}]
$$

#### Definition

Discrete Fréchet distance measures the similarity between two ordered paths.

It can be understood as the minimum leash length needed for two agents to walk along two paths from start to end without going backward.

In scanpath evaluation, the two paths are:

```text
predicted fixation sequence
human fixation sequence
```

#### Intuition

DTW accumulates alignment cost across the whole sequence.

Fréchet distance instead focuses on the worst distance encountered along the best possible traversal of the two paths.

```text
DTW      = accumulated alignment cost
Fréchet  = worst aligned distance along the best traversal
```

#### Formula

Let:

$$
P = [p_1, p_2, \ldots, p_n]
$$

and:

$$
G = [g_1, g_2, \ldots, g_m]
$$

The local point distance is:

$$
d(p_i, g_j) = \lVert p_i - g_j \rVert_2
$$

The discrete Fréchet distance is computed recursively as:

$$
C(i,j)
=
\max
\left(
d(p_i,g_j),
\min
\left(
C(i-1,j),
C(i-1,j-1),
C(i,j-1)
\right)
\right)
$$

The final distance is:

$$
\mathrm{Fr\acute{e}chet}
=
C(n,m)
$$

#### Interpretation

- `0.0` means identical ordered paths.
- Higher values mean the paths separate more strongly at some point.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{Fr\acute{e}chet} = 0
$$

#### Difference from DTW

DTW can remain low if most of the path aligns well, even if one part has a relatively large mismatch.

Fréchet distance is more sensitive to the largest mismatch along the best ordered alignment.

#### Limitation

Fréchet distance preserves path order, but it does not directly compare fixation durations or semantic AOIs. It is a geometric path metric.

---

### 9. Hausdorff Distance

#### Metric name

```text
hausdorff
```

#### Category

```text
alignment
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, \sqrt{2}]
$$

#### Definition

Hausdorff distance measures the spatial mismatch between two sets of fixation points.

Unlike DTW and Fréchet distance, Hausdorff distance ignores fixation order.

It asks:

```text
What is the largest nearest-neighbor distance between the two fixation sets?
```

#### Formula

Let \(P\) be the set of predicted fixation points and \(G\) be the set of human fixation points.

The directed Hausdorff distance from \(P\) to \(G\) is:

$$
h(P,G)
=
\max_{p \in P}
\min_{g \in G}
\lVert p - g \rVert_2
$$

The symmetric Hausdorff distance is:

$$
H(P,G)
=
\max
\left(
h(P,G),
h(G,P)
\right)
$$

#### Interpretation

- `0.0` means both fixation sets occupy the same spatial locations.
- Higher values mean at least one fixation is far from the other scanpath.

#### If prediction and human scanpath are exactly the same

$$
H(P,G) = 0
$$

#### Important limitation

Hausdorff distance ignores fixation order.

For example, these two scanpaths may have low Hausdorff distance:

```text
Human:     A -> B -> C
Predicted: C -> B -> A
```

because they contain the same fixation locations.

But their temporal order is opposite.

Therefore, Hausdorff should be used as a spatial coverage metric, not as a full scanpath-sequence metric.

### Alignment Metrics Summary

| Metric | Category | Direction | Preserves order? | Handles different lengths? | Main limitation |
|---|---|---|---|---|---|
| `dtw` | alignment | lower | yes, flexibly | yes | Can over-align repeated or stretched regions |
| `frechet` | alignment | lower | yes | yes | Sensitive to largest mismatch |
| `hausdorff` | alignment | lower | no | yes | Ignores temporal order |

---

## MultiMatch Metrics

MultiMatch is a multidimensional scanpath comparison method. Instead of returning one single similarity score, it compares scanpaths across several components.

In this project, MultiMatch is intended to be computed using the `multimatch-gaze` Python package, a Python implementation of the MultiMatch algorithm. If this package is unavailable and a fallback implementation is used, report the values as MultiMatch-style component metrics rather than exact MultiMatch.

MultiMatch compares scanpaths across five dimensions:

```text
shape
direction
length
position
duration
```

All MultiMatch metrics are similarity scores.

```text
1.0 = highly similar
0.0 = very different
```

The current implementation includes:

```text
multimatch_shape
multimatch_direction
multimatch_length
multimatch_position
multimatch_duration
```

### 10. MultiMatch Shape

#### Metric name

```text
multimatch_shape
```

#### Category

```text
multimatch
```

#### Direction

```text
higher is better
```

#### Range

$$
[0, 1]
$$

#### Definition

MultiMatch Shape compares the overall shape of the saccade-vector sequence.

It evaluates whether the predicted and human scanpaths have similar movement patterns when represented as sequences of saccade vectors.

#### Interpretation

- `1.0` means identical or highly similar scanpath shape.
- `0.0` means very different scanpath shape.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{MM}_{shape} = 1
$$

#### Limitation

This metric depends on the MultiMatch simplification and alignment procedure. It should be interpreted together with the other MultiMatch components rather than alone.

---

### 11. MultiMatch Direction

#### Metric name

```text
multimatch_direction
```

#### Category

```text
multimatch
```

#### Direction

```text
higher is better
```

#### Range

$$
[0, 1]
$$

#### Definition

MultiMatch Direction compares the directions of saccades in the predicted and human scanpaths.

It focuses on whether the eye movements follow similar angular directions, regardless of whether the exact fixation positions are identical.

#### Interpretation

- `1.0` means saccade directions are highly similar.
- `0.0` means saccade directions are very different.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{MM}_{direction} = 1
$$

#### Limitation

Direction similarity alone does not guarantee that scanpaths visit the same locations. Two scanpaths can move in similar directions but occur in different regions of the image.

---

### 12. MultiMatch Length

#### Metric name

```text
multimatch_length
```

#### Category

```text
multimatch
```

#### Direction

```text
higher is better
```

#### Range

$$
[0, 1]
$$

#### Definition

MultiMatch Length compares the lengths, or amplitudes, of saccades in the predicted and human scanpaths.

It evaluates whether the predicted eye movements have similar movement magnitudes to the human scanpath.

#### Interpretation

- `1.0` means saccade lengths are highly similar.
- `0.0` means saccade lengths are very different.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{MM}_{length} = 1
$$

#### Limitation

Length similarity does not capture direction or spatial position. Two scanpaths may have similar saccade lengths but move in different directions or visit different regions.

---

### 13. MultiMatch Position

#### Metric name

```text
multimatch_position
```

#### Category

```text
multimatch
```

#### Direction

```text
higher is better
```

#### Range

$$
[0, 1]
$$

#### Definition

MultiMatch Position compares the spatial positions of fixations in the predicted and human scanpaths.

It evaluates whether the two scanpaths visit similar image regions.

#### Interpretation

- `1.0` means fixation positions are highly similar.
- `0.0` means fixation positions are very different.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{MM}_{position} = 1
$$

#### Limitation

Position similarity does not fully describe the temporal order of fixations. It should be interpreted together with shape, direction, and sequence-based metrics.

---

### 14. MultiMatch Duration

#### Metric name

```text
multimatch_duration
```

#### Category

```text
multimatch
```

#### Direction

```text
higher is better
```

#### Range

$$
[0, 1]
$$

The metric may return `NaN` when valid durations are unavailable.

#### Definition

MultiMatch Duration compares the fixation durations in the predicted and human scanpaths.

It evaluates whether the two scanpaths have similar fixation timing patterns.

#### Interpretation

- `1.0` means fixation durations are highly similar.
- `0.0` means fixation durations are very different.
- `NaN` means duration comparison is not possible.

#### If prediction and human scanpath are exactly the same

If valid durations are available:

$$
\mathrm{MM}_{duration} = 1
$$

If valid durations are not available, the metric may return:

```text
NaN
```

#### Limitation

This metric requires meaningful fixation durations. If predicted scanpaths use fixed or artificial durations, this component should be interpreted carefully.

### MultiMatch Metrics Summary

| Metric | Category | Direction | Range | What it compares |
|---|---|---|---|---|
| `multimatch_shape` | multimatch | higher | `[0, 1]` | Overall saccade-vector shape |
| `multimatch_direction` | multimatch | higher | `[0, 1]` | Saccade directions |
| `multimatch_length` | multimatch | higher | `[0, 1]` | Saccade amplitudes |
| `multimatch_position` | multimatch | higher | `[0, 1]` | Fixation positions |
| `multimatch_duration` | multimatch | higher | `[0, 1]` or `NaN` | Fixation durations |

---

## Symbolic / Grid-AOI Metrics

Symbolic metrics convert scanpaths from continuous fixation coordinates into discrete grid-based AOI sequences.

In this benchmark, AOI means **grid AOI**, not semantic AOI. The image is divided into a fixed grid, for example:

```text
12 columns x 8 rows = 96 grid AOIs
```

Each fixation is assigned to one grid cell based on its normalized `(x, y)` coordinate. The scanpath then becomes a sequence of grid AOI IDs.

For example:

```text
Fixations:
[(0.10, 0.20), (0.30, 0.25), (0.70, 0.80)]

Grid AOI sequence:
[13, 27, 91]
```

These metrics are useful when the exact fixation coordinates are less important than the sequence of visited regions.

The current implementation includes:

```text
scanmatch
levenshtein
needleman_wunsch
aoi_transition_similarity
sequence_score
```

### 15. ScanMatch

#### Metric name

```text
scanmatch
```

#### Category

```text
symbolic
```

#### Direction

```text
higher is better
```

#### Range

$$
[0, 1]
$$

in the current implementation.

#### Definition

ScanMatch compares two scanpaths after converting fixation coordinates into grid-AOI sequences.

The current implementation is a Python ScanMatch-style implementation:

```text
fixation coordinates
-> grid-AOI sequence
-> Needleman-Wunsch alignment
-> spatial substitution score
```

It gives higher scores when two scanpaths visit similar grid cells in a similar order.

#### Formula

Let the predicted scanpath be converted to a grid-AOI sequence:

$$
S^{p} = [s^{p}_{1}, s^{p}_{2}, \ldots, s^{p}_{n}]
$$

and the human scanpath be converted to:

$$
S^{g} = [s^{g}_{1}, s^{g}_{2}, \ldots, s^{g}_{m}]
$$

where each \(s_i\) is a grid-AOI ID.

ScanMatch computes a global alignment score:

$$
\mathrm{ScanMatch}
=
\frac{
\mathrm{AlignmentScore}(S^{p}, S^{g})
}
{
\mathrm{MaximumPossibleScore}
}
$$

In this implementation, the alignment is computed using a Needleman-Wunsch-style global alignment with spatially informed substitution scores.

#### Interpretation

- `1.0` means highly similar grid-AOI sequences.
- `0.0` means very different grid-AOI sequences.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{ScanMatch} = 1
$$

#### Important note

This implementation follows the main idea of ScanMatch but is not the official MATLAB ScanMatch toolbox.

#### Limitation

The result depends on the grid resolution. A finer grid makes the metric more sensitive to small spatial differences, while a coarser grid makes it more tolerant.

---

### 16. Levenshtein Distance

#### Metric name

```text
levenshtein
```

#### Category

```text
symbolic
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, \max(n, m)]
$$

where \(n\) and \(m\) are the lengths of the predicted and human AOI sequences.

#### Definition

Levenshtein distance measures the minimum number of edits needed to transform one grid-AOI sequence into another.

Allowed edit operations are:

```text
insertion
deletion
substitution
```

#### Formula

Let:

$$
S^{p} = [s^{p}_{1}, s^{p}_{2}, \ldots, s^{p}_{n}]
$$

and:

$$
S^{g} = [s^{g}_{1}, s^{g}_{2}, \ldots, s^{g}_{m}]
$$

The Levenshtein distance is the minimum number of edit operations required to transform \(S^{p}\) into \(S^{g}\):

$$
\mathrm{LEV}(S^{p}, S^{g})
=
\min
\left(
\#\mathrm{insertions}
+
\#\mathrm{deletions}
+
\#\mathrm{substitutions}
\right)
$$

#### Interpretation

- `0` means identical grid-AOI sequences.
- Higher values mean more edits are needed.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{LEV} = 0
$$

#### Limitation

Levenshtein distance treats all substitutions equally. For example, substituting a neighboring grid cell and substituting a far-away grid cell both count as one edit. ScanMatch addresses this limitation by using spatially informed substitution scores.

---

### 17. Needleman-Wunsch Similarity

#### Metric name

```text
needleman_wunsch
```

#### Category

```text
symbolic
```

#### Direction

```text
higher is better
```

#### Range

$$
[0, 1]
$$

in the current implementation.

#### Definition

Needleman-Wunsch is a global sequence-alignment method.

In this benchmark, it aligns two grid-AOI sequences and gives higher scores when the two scanpaths visit similar AOIs in a similar order.

#### Formula

Let the predicted and human AOI sequences be \(S^p\) and \(S^g\).

The global alignment score is computed recursively:

$$
D(i,j)
=
\max
\left(
D(i-1,j) + \gamma,
D(i,j-1) + \gamma,
D(i-1,j-1) + \mathrm{sub}(s^p_i, s^g_j)
\right)
$$

where:

- \(\gamma\) is the gap penalty
- \(\mathrm{sub}(s^p_i, s^g_j)\) is the substitution score between two grid AOIs

The final normalized similarity is:

$$
\mathrm{NW}
=
\frac{
D(n,m)
}
{
\mathrm{MaximumPossibleScore}
}
$$

#### Interpretation

- `1.0` means strong sequence alignment.
- `0.0` means weak sequence alignment.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{NW} = 1
$$

#### Limitation

The score depends on the chosen substitution matrix, gap penalty, and grid resolution.

---

### 18. AOI Transition Similarity

#### Metric name

```text
aoi_transition_similarity
```

#### Category

```text
symbolic
```

#### Direction

```text
higher is better
```

#### Range

$$
[0, 1]
$$

The metric may return `NaN` if there are not enough fixations to form transitions.

#### Definition

AOI Transition Similarity compares the transition patterns between grid AOIs.

A transition is an ordered pair:

```text
AOI_i -> AOI_{i+1}
```

The metric builds a transition-count vector for the predicted scanpath and another transition-count vector for the human scanpath. It then computes cosine similarity between these two vectors.

#### Formula

Let \(T^p\) be the transition-count vector for the predicted scanpath, and \(T^g\) be the transition-count vector for the human scanpath.

AOI Transition Similarity is:

$$
\mathrm{AOITransSim}
=
\frac{
T^p \cdot T^g
}
{
\lVert T^p \rVert_2
\lVert T^g \rVert_2
}
$$

#### Interpretation

- `1.0` means the same transition pattern.
- `0.0` means no shared transition structure.

#### If prediction and human scanpath are exactly the same

If at least one transition exists:

$$
\mathrm{AOITransSim} = 1
$$

If there are not enough fixations to form transitions, the metric may return:

```text
NaN
```

#### Limitation

This metric compares transition counts, not exact fixation timing. It is also sensitive to the grid resolution.

---

### 19. Sequence Score

#### Metric name

```text
sequence_score
```

#### Category

```text
symbolic
```

#### Direction

```text
higher is better
```

#### Range

$$
[0, 1]
$$

#### Definition

Sequence Score measures the similarity between predicted and human grid-AOI sequences using normalized Levenshtein distance.

It converts the edit distance into a similarity score.

#### Formula

Let:

$$
\mathrm{LEV}(S^{p}, S^{g})
$$

be the Levenshtein distance between predicted and human AOI sequences.

Let:

$$
L = \max(n, m)
$$

where \(n\) and \(m\) are the two sequence lengths.

Then Sequence Score is:

$$
\mathrm{SequenceScore}
=
1
-
\frac{
\mathrm{LEV}(S^{p}, S^{g})
}
{
L
}
$$

#### Interpretation

- `1.0` means identical grid-AOI sequences.
- `0.0` means maximally different grid-AOI sequences under this normalization.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{SequenceScore} = 1
$$

#### Important note

This metric uses grid-based AOIs, not semantic AOIs. It does not require annotations such as title, axis, legend, mark, button, or menu regions.

#### Limitation

The score depends on the chosen grid resolution. A finer grid makes the metric more sensitive to small spatial differences, while a coarser grid makes it more tolerant.

### Symbolic / Grid-AOI Metrics Summary

| Metric | Category | Direction | Range | What it compares |
|---|---|---|---|---|
| `scanmatch` | symbolic | higher | `[0, 1]` | Grid-AOI sequence alignment |
| `levenshtein` | symbolic | lower | `[0, max(n, m)]` | Edit distance between grid-AOI sequences |
| `needleman_wunsch` | symbolic | higher | `[0, 1]` | Global alignment of grid-AOI sequences |
| `aoi_transition_similarity` | symbolic | higher | `[0, 1]` or `NaN` | Similarity of AOI transition patterns |
| `sequence_score` | symbolic | higher | `[0, 1]` | Normalized AOI-sequence similarity |

---

## Scanpath Statistics

Scanpath statistics describe properties of the predicted scanpath itself.

Unlike most metrics in this document, these are not direct prediction-vs-human similarity metrics. They are descriptive measures that help check whether generated scanpaths have realistic properties.

The current implementation includes:

```text
number_of_fixations
aoi_transition_count
```

### 20. Number of Fixations

#### Metric name

```text
number_of_fixations
```

#### Category

```text
scanpath-statistic
```

#### Direction

```text
descriptive
```

#### Range

$$
[0, +\infty)
$$

The value is a non-negative integer.

#### Definition

Number of Fixations counts how many fixations are present in the predicted scanpath.

This metric is computed only from the predicted scanpath.

#### Formula

Let the predicted scanpath be:

$$
P = [p_1, p_2, \ldots, p_n]
$$

where each \(p_i\) is a predicted fixation.

Then:

$$
\mathrm{NumberOfFixations} = n
$$

#### Interpretation

- Larger values mean more fixations in the predicted scanpath.
- Smaller values mean fewer fixations in the predicted scanpath.

This statistic is useful for checking whether a model or sampler generates scanpaths with realistic length.

For example, if human scanpaths usually contain around 10 fixations but the model consistently generates 3 or 30, this indicates a mismatch in scanpath length.

#### If prediction and human scanpath are exactly the same

If the scanpath contains \(N\) fixations:

$$
\mathrm{NumberOfFixations} = N
$$

#### Limitation

This is a descriptive statistic, not a similarity metric.

In the current implementation, it is computed only on the predicted scanpath. To interpret it properly, compare the predicted distribution of fixation counts against the human distribution.

---

### 21. AOI Transition Count

#### Metric name

```text
aoi_transition_count
```

#### Category

```text
scanpath-statistic
```

#### Direction

```text
descriptive
```

#### Range

$$
[0, N - 1]
$$

where \(N\) is the number of fixations in the predicted scanpath.

#### Definition

AOI Transition Count measures how many times the predicted scanpath moves from one grid AOI to another.

The image is divided into grid-based AOIs. Each fixation is assigned to one grid cell. A transition is counted when two consecutive fixations belong to different grid cells.

#### Formula

Let the predicted grid-AOI sequence be:

$$
S^p = [s^p_1, s^p_2, \ldots, s^p_N]
$$

where \(s^p_i\) is the grid-AOI ID of fixation \(i\).

The AOI transition count is:

$$
\mathrm{AOITransitionCount}
=
\sum_{i=1}^{N-1}
\mathbf{1}
\left[
s^p_i \neq s^p_{i+1}
\right]
$$

where \(\mathbf{1}[\cdot]\) is the indicator function, equal to 1 when the condition is true and 0 otherwise.

#### Example

For the AOI sequence:

```text
[13, 13, 27, 40, 40, 52]
```

The counted transitions are:

```text
13 -> 27
27 -> 40
40 -> 52
```

So:

$$
\mathrm{AOITransitionCount} = 3
$$

#### Interpretation

- Larger values mean the scanpath moves across more grid AOIs.
- Smaller values mean the scanpath stays within fewer grid AOIs.

#### If prediction and human scanpath are exactly the same

The value is the number of grid-AOI changes in the predicted scanpath.

For a scanpath with \(N\) fixations, the value is between:

$$
0
\leq
\mathrm{AOITransitionCount}
\leq
N - 1
$$

#### Important note

This metric uses grid-based AOIs, not semantic AOIs.

It can be computed from normalized fixation coordinates alone. It does not require manually annotated AOI labels.

#### Limitation

This is a descriptive statistic, not a direct similarity metric. It should be compared against human scanpath statistics rather than interpreted as simply better or worse.

The result depends on the grid resolution. A finer grid will usually produce more AOI transitions; a coarser grid will usually produce fewer transitions.

### Scanpath Statistics Summary

| Metric | Category | Direction | Range | What it describes |
|---|---|---|---|---|
| `number_of_fixations` | scanpath-statistic | descriptive | `[0, +inf)` | Length of the predicted scanpath |
| `aoi_transition_count` | scanpath-statistic | descriptive | `[0, N - 1]` | Number of grid-AOI changes in the predicted scanpath |

---

## Spatial Set-based Metrics

Spatial set-based metrics compare the spatial distribution of fixation points.

Unlike point-wise and alignment-based metrics, these metrics mostly ignore fixation order. They are useful for checking whether two scanpaths cover similar image regions, even if the sequence of fixations is different.

The current implementation includes:

```text
eyenalysis
mannan_distance
```

### 22. Eyenalysis

#### Metric name

```text
eyenalysis
```

#### Category

```text
spatial
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, \sqrt{2}]
$$

#### Definition

Eyenalysis-style distance compares two scanpaths as sets of fixation points.

It measures the symmetric nearest-neighbor spatial mismatch between predicted and human fixations.

For each predicted fixation, it finds the nearest human fixation. For each human fixation, it finds the nearest predicted fixation. The final score is the average of these two nearest-neighbor distances.

#### Formula

Let the predicted fixation set be:

$$
P = \{p_1, p_2, \ldots, p_n\}
$$

and the human fixation set be:

$$
G = \{g_1, g_2, \ldots, g_m\}
$$

where each fixation is a 2D point.

The predicted-to-human nearest-neighbor distance is:

$$
d(P, G)
=
\frac{1}{n}
\sum_{i=1}^{n}
\min_{g_j \in G}
\lVert p_i - g_j \rVert_2
$$

The human-to-predicted nearest-neighbor distance is:

$$
d(G, P)
=
\frac{1}{m}
\sum_{j=1}^{m}
\min_{p_i \in P}
\lVert g_j - p_i \rVert_2
$$

The symmetric Eyenalysis-style distance is:

$$
\mathrm{Eyenalysis}
=
\frac{
d(P, G) + d(G, P)
}
{2}
$$

#### Interpretation

- `0.0` means fixation sets overlap closely.
- Higher values mean larger spatial mismatch.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{Eyenalysis} = 0
$$

#### Limitation

This metric ignores fixation order.

For example, these two scanpaths can have low Eyenalysis distance:

```text
Human:     A -> B -> C
Predicted: C -> B -> A
```

because they visit the same locations, even though the order is reversed.

Therefore, Eyenalysis should be interpreted as a spatial coverage metric, not as a full sequence metric.

---

### 23. Mannan Distance / Similarity

#### Metric name

```text
mannan_distance
```

#### Category

```text
spatial
```

#### Direction

```text
higher is better
```

#### Range

$$
[0, 1]
$$

in the current implementation.

#### Definition

The Mannan-style metric compares the spatial mismatch between two fixation sets against a random baseline.

In the current implementation, it is treated as a similarity score:

```text
1.0 = highly similar fixation sets
0.0 = no better than random baseline
```

Like Eyenalysis, this metric focuses on spatial distribution and mostly ignores fixation order.

#### Formula

First, a spatial dissimilarity \(D(P, G)\) is computed between the predicted fixation set \(P\) and the human fixation set \(G\), based on nearest-neighbor distances.

Let:

$$
P = \{p_1, p_2, \ldots, p_n\}
$$

and:

$$
G = \{g_1, g_2, \ldots, g_m\}
$$

The dissimilarity is computed as:

$$
D(P, G)
=
\frac{
m \sum_{i=1}^{n}
\left(
\min_{g_j \in G}
\lVert p_i - g_j \rVert_2
\right)^2
+
n \sum_{j=1}^{m}
\left(
\min_{p_i \in P}
\lVert g_j - p_i \rVert_2
\right)^2
}
{
4nm
}
$$

In this implementation, coordinates are normalized to \([0, 1]\), so the normalization assumes an image width and height of 1.

The observed dissimilarity is compared against a random baseline:

$$
\mathrm{MannanSimilarity}
=
1
-
\frac{
D(P, G)
}
{
D_{\mathrm{random}}
}
$$

The final value is clipped to the interval:

$$
[0, 1]
$$

#### Interpretation

- `1.0` means predicted and human fixation sets are highly similar.
- `0.0` means predicted fixation set is no better than the random baseline.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{MannanSimilarity} = 1
$$

#### Important note

Although the metric name in the code is:

```text
mannan_distance
```

the current implementation returns a **similarity score**, not a raw distance.

For clarity in future versions, this metric could be renamed to:

```text
mannan_similarity
```

or documented as:

```text
mannan_distance = Mannan-style spatial similarity
```

#### Limitation

This metric ignores fixation order and depends on the random baseline used for normalization.

Because the baseline is estimated from random scanpaths, results may vary slightly unless the random seed is fixed.

### Spatial Set-based Metrics Summary

| Metric | Category | Direction | Range | What it compares |
|---|---|---|---|---|
| `eyenalysis` | spatial | lower | `[0, sqrt(2)]` | Symmetric nearest-neighbor spatial mismatch |
| `mannan_distance` | spatial | higher | `[0, 1]` | Spatial similarity relative to a random baseline |

---

## Recurrence-based Metrics

Recurrence-based metrics analyze repeated spatial states in scanpaths using a cross-recurrence matrix.

A fixation pair is considered recurrent if the predicted fixation and the human fixation are spatially close according to a distance threshold.

In the current implementation, the default threshold is:

```text
0.05
```

Because coordinates are normalized to `[0, 1]`, this means that two fixations are considered recurrent if they are within approximately 5% of the normalized image scale.

The current implementation includes:

```text
recurrence
determinism
laminarity
corm
```

These metrics are descriptive. Higher or lower values are not always directly “better.” They should be interpreted by comparing predicted scanpaths against human scanpath distributions.

### 24. Recurrence

#### Metric name

```text
recurrence
```

#### Category

```text
recurrence
```

#### Direction

```text
descriptive
```

#### Range

$$
[0, 100]
$$

#### Definition

Recurrence measures the percentage of predicted-human fixation pairs that are spatially close.

A cross-recurrence matrix is first constructed. Each cell indicates whether a predicted fixation and a human fixation are closer than the recurrence threshold.

#### Formula

Let the predicted scanpath be:

$$
P = [p_1, p_2, \ldots, p_n]
$$

and the human scanpath be:

$$
G = [g_1, g_2, \ldots, g_m]
$$

where each fixation is a 2D point.

The cross-recurrence matrix \(R\) is defined as:

$$
R_{ij}
=
\begin{cases}
1, & \text{if } \lVert p_i - g_j \rVert_2 < \epsilon \\
0, & \text{otherwise}
\end{cases}
$$

where \(\epsilon\) is the recurrence threshold.

The recurrence rate is:

$$
\mathrm{REC}
=
100
\cdot
\frac{
\sum_{i=1}^{n}
\sum_{j=1}^{m}
R_{ij}
}
{
nm
}
$$

#### Interpretation

- `0` means no recurrent fixation pairs.
- `100` means every predicted-human fixation pair is recurrent.

A higher value means more spatial overlap between the predicted and human scanpaths, but it should be interpreted descriptively.

#### If prediction and human scanpath are exactly the same

If the scanpath has \(N\) fixations and only diagonal self-matches are recurrent, then:

$$
\mathrm{REC}
=
\frac{100}{N}
$$

For example, if \(N = 4\):

$$
\mathrm{REC}
=
25
$$

If the threshold is large enough that many off-diagonal pairs are also recurrent, recurrence can be higher.

#### Limitation

Recurrence is highly sensitive to the spatial threshold \(\epsilon\). A small threshold may produce very few recurrent points, while a large threshold may make many fixations recurrent.

---

### 25. Determinism

#### Metric name

```text
determinism
```

#### Category

```text
recurrence
```

#### Direction

```text
descriptive
```

#### Range

$$
[0, 100]
$$

The metric may return `NaN` if there are no recurrent points.

#### Definition

Determinism measures the percentage of recurrent points that form diagonal lines in the cross-recurrence matrix.

Diagonal lines indicate that the two scanpaths contain similar sequential structure.

#### Formula

Let \(R\) be the cross-recurrence matrix.

Let:

$$
N_{\mathrm{rec}}
=
\sum_{i=1}^{n}
\sum_{j=1}^{m}
R_{ij}
$$

be the total number of recurrent points.

Let:

$$
N_{\mathrm{diag}}
$$

be the number of recurrent points that belong to diagonal line segments of at least length \(l_{\min}\).

Then determinism is:

$$
\mathrm{DET}
=
100
\cdot
\frac{
N_{\mathrm{diag}}
}
{
N_{\mathrm{rec}}
}
$$

In the current implementation, the default minimum line length is:

```text
2
```

#### Interpretation

- High `DET` means recurrent points form sequential diagonal structure.
- Low `DET` means recurrent points are scattered.
- `NaN` means no recurrent points exist.

#### If prediction and human scanpath are exactly the same

If recurrent points form a diagonal line, then:

$$
\mathrm{DET} = 100
$$

For very short scanpaths, determinism can easily become extreme, such as `100`, because the recurrence matrix is small.

#### Limitation

Determinism depends on the recurrence threshold and the minimum diagonal-line length. It is also less stable for very short scanpaths.

---

### 26. Laminarity

#### Metric name

```text
laminarity
```

#### Category

```text
recurrence
```

#### Direction

```text
descriptive
```

#### Range

$$
[0, 100]
$$

The metric may return `NaN` if there are no recurrent points.

#### Definition

Laminarity measures the percentage of recurrent points that form horizontal or vertical lines in the cross-recurrence matrix.

Horizontal or vertical line structures can indicate repeated or stable fixation states.

#### Formula

Let:

$$
N_{\mathrm{rec}}
$$

be the total number of recurrent points.

Let:

$$
N_{\mathrm{hor}}
$$

be the number of recurrent points that belong to horizontal line segments of at least length \(l_{\min}\).

Let:

$$
N_{\mathrm{ver}}
$$

be the number of recurrent points that belong to vertical line segments of at least length \(l_{\min}\).

Then laminarity is:

$$
\mathrm{LAM}
=
100
\cdot
\frac{
N_{\mathrm{hor}} + N_{\mathrm{ver}}
}
{
2N_{\mathrm{rec}}
}
$$

The factor of \(2\) is used because both horizontal and vertical structures are counted.

#### Interpretation

- High `LAM` means many recurrent points form horizontal or vertical structures.
- Low `LAM` means recurrent points do not form stable or repeated-state structures.
- `NaN` means no recurrent points exist.

#### If prediction and human scanpath are exactly the same

For simple one-to-one diagonal matches, laminarity is often:

$$
\mathrm{LAM} = 0
$$

because the recurrent points form a diagonal line rather than horizontal or vertical lines.

#### Limitation

Laminarity is sensitive to the recurrence threshold and scanpath length. It should be interpreted as a descriptive structural metric rather than a direct model accuracy score.

---

### 27. CORM

#### Metric name

```text
corm
```

#### Category

```text
recurrence
```

#### Direction

```text
descriptive
```

#### Range

$$
[0, 100]
$$

The metric may return `NaN` if there are no recurrent points.

#### Definition

CORM means **center of recurrence mass**.

It measures the average temporal displacement of recurrent points from the main diagonal of the recurrence matrix.

The main diagonal corresponds to recurrence at similar relative time positions. Points far from the diagonal indicate recurrence with a temporal shift.

#### Formula

Let \(R_{ij} = 1\) indicate a recurrent point.

The normalized time position of predicted fixation \(i\) is:

$$
t^p_i
=
\frac{i}{n - 1}
$$

and the normalized time position of human fixation \(j\) is:

$$
t^g_j
=
\frac{j}{m - 1}
$$

For each recurrent point, the temporal displacement is:

$$
\left| t^p_i - t^g_j \right|
$$

CORM is computed as:

$$
\mathrm{CORM}
=
100
\cdot
\frac{
1
}{
N_{\mathrm{rec}}
}
\sum_{(i,j): R_{ij}=1}
\left|
t^p_i - t^g_j
\right|
$$

#### Interpretation

- `0` means recurrent points lie on the main diagonal.
- A high value means recurrence occurs with stronger temporal displacement.
- `NaN` means no recurrent points exist.

#### If prediction and human scanpath are exactly the same

If recurrent points lie on the main diagonal:

$$
\mathrm{CORM} = 0
$$

#### Limitation

CORM depends on the recurrence threshold and the number of recurrent points. If there are very few recurrent points, the value may be unstable.

### Recurrence-based Metrics Summary

| Metric | Category | Direction | Range | What it describes |
|---|---|---|---|---|
| `recurrence` | recurrence | descriptive | `[0, 100]` | Percentage of spatially close fixation pairs |
| `determinism` | recurrence | descriptive | `[0, 100]` or `NaN` | Diagonal structure in recurrence matrix |
| `laminarity` | recurrence | descriptive | `[0, 100]` or `NaN` | Horizontal/vertical repeated-state structure |
| `corm` | recurrence | descriptive | `[0, 100]` or `NaN` | Temporal displacement of recurrent points |

---

## Temporal Embedding Metrics

Temporal embedding metrics compare local subsequences of scanpaths.

Instead of comparing individual fixations one by one, these metrics compare short windows of consecutive fixations. This helps capture local scanpath dynamics, such as short movement patterns over several fixations.

The current implementation includes:

```text
tde
scaled_tde
```

### 28. Time-Delay Embedding Distance

#### Metric name

```text
tde
```

#### Category

```text
temporal-embedding
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, \sqrt{2}]
$$

approximately, because fixation coordinates are normalized.

#### Definition

Time-Delay Embedding distance compares local \(k\)-fixation subsequences between the predicted and human scanpaths.

For example, if \(k = 3\), the scanpath is converted into overlapping subsequences:

```text
[f1, f2, f3]
[f2, f3, f4]
[f3, f4, f5]
...
```

Each subsequence represents a short local scanpath pattern.

#### Formula

Let the predicted scanpath be:

$$
P = [p_1, p_2, \ldots, p_n]
$$

and the human scanpath be:

$$
G = [g_1, g_2, \ldots, g_m]
$$

where each fixation is a 2D point.

For embedding dimension \(k\), the predicted time-delay vectors are:

$$
V^p_i =
[p_i, p_{i+1}, \ldots, p_{i+k-1}]
$$

for:

$$
i = 1, 2, \ldots, n-k+1
$$

The human time-delay vectors are:

$$
V^g_j =
[g_j, g_{j+1}, \ldots, g_{j+k-1}]
$$

for:

$$
j = 1, 2, \ldots, m-k+1
$$

The distance between two embedded vectors is computed as the mean Euclidean distance between corresponding fixations:

$$
d(V^p_i, V^g_j)
=
\frac{1}{k}
\sum_{r=0}^{k-1}
\left\|
p_{i+r} - g_{j+r}
\right\|_2
$$

For each predicted embedded vector, the closest human embedded vector is found. For each human embedded vector, the closest predicted embedded vector is also found.

The TDE distance is:

$$
\mathrm{TDE}
=
\frac{1}{2}
\left(
\frac{1}{N_p}
\sum_{i=1}^{N_p}
\min_j d(V^p_i, V^g_j)
+
\frac{1}{N_g}
\sum_{j=1}^{N_g}
\min_i d(V^g_j, V^p_i)
\right)
$$

where:

$$
N_p = n-k+1
$$

and:

$$
N_g = m-k+1
$$

#### Interpretation

- `0.0` means very similar local temporal patterns.
- Higher values mean larger difference in local scanpath dynamics.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{TDE} = 0
$$

#### Limitation

TDE requires each scanpath to have at least \(k\) fixations. If a scanpath is shorter than \(k\), the metric returns `NaN`.

The result also depends on the choice of \(k\). Larger \(k\) captures longer local patterns but requires longer scanpaths.

---

### 29. Scaled Time-Delay Embedding Distance

#### Metric name

```text
scaled_tde
```

#### Category

```text
temporal-embedding
```

#### Direction

```text
lower is better
```

#### Range

$$
[0, 1]
$$

approximately, because the raw TDE value is normalized by the maximum possible normalized spatial distance.

#### Definition

Scaled TDE is a normalized version of TDE.

Because the maximum possible distance between two normalized fixation points is:

$$
\sqrt{2}
$$

Scaled TDE divides the raw TDE distance by \(\sqrt{2}\).

#### Formula

$$
\mathrm{ScaledTDE}
=
\frac{
\mathrm{TDE}
}
{
\sqrt{2}
}
$$

#### Interpretation

- `0.0` means very similar local temporal patterns.
- Higher values mean larger difference in local scanpath dynamics.

Because this metric is normalized, it is easier to compare across datasets.

#### If prediction and human scanpath are exactly the same

$$
\mathrm{ScaledTDE} = 0
$$

#### Limitation

Like TDE, Scaled TDE depends on the embedding dimension \(k\) and requires scanpaths to contain at least \(k\) fixations.

### Temporal Embedding Metrics Summary

| Metric | Category | Direction | Range | What it compares |
|---|---|---|---|---|
| `tde` | temporal-embedding | lower | approximately `[0, sqrt(2)]` | Local \(k\)-fixation subsequence patterns |
| `scaled_tde` | temporal-embedding | lower | approximately `[0, 1]` | Normalized local \(k\)-fixation subsequence patterns |

---

## Implementation Notes

All scanpath metrics are implemented in:

```text
src/scanpath/metrics.py
```

Each metric is registered in the `SCANPATH_METRICS` registry with metadata describing how the metric should be interpreted.

The registry uses the `ScanpathMetric` dataclass defined in:

```text
src/scanpath/registry.py
```

Each metric entry includes:

```text
name
function
category
direction
description
requires_duration
```

Example registry entry:

```python
"mean_fixation_error": ScanpathMetric(
    name="mean_fixation_error",
    function=mean_fixation_error,
    category="pointwise",
    direction="lower",
    description=(
        "Mean Euclidean distance between corresponding predicted "
        "and human fixations."
    ),
)
```

The metric registry makes the evaluation output easier to interpret because every result row includes both the metric value and its metadata.

For example, the raw output should contain:

```text
image_id, prediction_id, subject_id, model, sampler, metric, category, direction, value
```

This makes it clear whether a metric should be minimized, maximized, or interpreted descriptively.

If the current debug evaluator does not yet include `prediction_id` in the output, this should be added before running human group-vs-human group evaluation or multi-sample model evaluation.

---

## Evaluation Output

The evaluation pipeline produces two levels of output:

```text
raw metric results
summary metric results
```

### Raw metric results

The raw result file stores one row per comparison between a predicted scanpath and a human subject scanpath.

Example columns:

```text
image_id, prediction_id, subject_id, model, sampler, metric, category, direction, value
```

Example row:

```text
img001, good_001, s01, dummy_good, dummy_sampler, mean_fixation_error, pointwise, lower, 0.014142
```

This means that prediction `good_001` from `dummy_good` was compared against subject `s01` for image `img001` using `mean_fixation_error`.

### Summary metric results

The summary result file aggregates metric values across human subjects.

Example columns:

```text
image_id, model, sampler, metric, mean, std, n_subjects, n_valid, median, min, max
```

where:

```text
n_subjects = number of human subjects compared against
n_valid    = number of non-NaN metric values
```

The distinction between `n_subjects` and `n_valid` is important because some metrics can return `NaN`.

For example, `duration_correlation` can return `NaN` if one duration sequence has zero variance. Recurrence-derived metrics can also return `NaN` if there are no recurrent points.

---

## Aggregation Strategy

Each predicted scanpath is compared against each available human scanpath for the same image.

For example:

```text
prediction vs subject_01
prediction vs subject_02
prediction vs subject_03
```

The raw file stores all subject-level comparisons.

The summary file aggregates these subject-level comparisons using:

```text
mean
standard deviation
median
minimum
maximum
number of subjects
number of valid values
```

For full experiments, aggregation should follow this hierarchy:

```text
subject-level comparisons
-> image-level aggregation
-> dataset-level aggregation
```

The model should not be evaluated using only the best-matching human subject because that would make the model look artificially better.

Instead, the model should be evaluated against the distribution of human scanpaths.

---

## Recommended Aggregation Function

The aggregation function should keep both the number of subjects and the number of valid metric values:

```python
from __future__ import annotations

import pandas as pd


def aggregate_scanpath_results(results: pd.DataFrame) -> pd.DataFrame:
    grouped = results.groupby(
        ["image_id", "model", "sampler", "metric"],
        as_index=False,
    )

    return grouped.agg(
        mean=("value", "mean"),
        std=("value", "std"),
        n_subjects=("subject_id", "nunique"),
        n_valid=("value", "count"),
        median=("value", "median"),
        min=("value", "min"),
        max=("value", "max"),
    )
```

The `n_valid` column is useful because descriptive or correlation-based metrics may return `NaN`.

For example:

```text
n_subjects = 2
n_valid = 0
```

means that two subjects were compared, but the metric was undefined for both comparisons.

If multiple `prediction_id` values exist per image/model/sampler, consider including `prediction_id` in the grouping for sample-level summaries:

```python
["image_id", "prediction_id", "model", "sampler", "metric"]
```

Then aggregate across prediction samples in a second stage.

---

## Dummy Validation Tests

Before applying the metrics to real datasets, we validate them using controlled dummy scanpaths.

The goal is to check whether each metric behaves in the expected direction before using the metrics on UEyes, MASSVIS, or model-generated scanpaths.

The debug setup uses one human scanpath file and three prediction files:

```text
data/processed/debug/human_scanpaths.csv
data/processed/debug/pred_same.csv
data/processed/debug/pred_good.csv
data/processed/debug/pred_bad.csv
```

The evaluation script is:

```text
scripts/run_debug_scanpath_eval.py
```

Running the script produces raw and summary results under:

```text
results/metrics/debug/
```

### Dummy prediction cases

| Case | File | Description | Expected behavior |
|---|---|---|---|
| `same` | `pred_same.csv` | Prediction is exactly identical to subject `s01` | Perfect values against `s01` |
| `good` | `pred_good.csv` | Prediction is slightly shifted from the human scanpaths | Small errors and high similarities |
| `bad` | `pred_bad.csv` | Prediction is spatially far and follows a different direction | Larger errors and lower similarities |

### Expected metric behavior

For distance or error metrics, lower values are better. Therefore, the expected pattern is:

```text
same < good < bad
```

For similarity metrics, higher values are better. Therefore, the expected pattern is:

```text
same > good > bad
```

For descriptive metrics, there is no universal better or worse direction. These metrics should be interpreted structurally:

```text
number_of_fixations
aoi_transition_count
recurrence
determinism
laminarity
corm
```

### Important note about the `same` case

In the `same` dummy condition, the prediction is identical to subject `s01`.

Therefore, metrics against `s01` should show perfect agreement:

```text
error / distance metrics = 0
similarity metrics = 1
```

However, the aggregated summary for the `same` case is not necessarily perfect, because the summary averages over both `s01` and `s02`.

The prediction is identical to `s01`, but not identical to `s02`.

So this is expected:

```text
raw same vs s01     = perfect
raw same vs s02     = not perfect
summary same result = average of both comparisons
```

### Expected values for identical scanpaths

When the predicted scanpath and human scanpath are exactly the same, the expected values are:

| Metric type | Expected value |
|---|---|
| Distance / error metrics | `0.0` |
| Similarity metrics | `1.0` |
| Levenshtein distance | `0.0` |
| Duration correlation | `1.0` if durations have non-zero variance; otherwise `NaN` |
| Number of fixations | `N`, where `N` is the number of predicted fixations |
| AOI transition count | Number of grid-AOI changes in the predicted scanpath |
| Recurrence | Depends on threshold and scanpath length |
| Determinism | Usually `100.0` if recurrent points form a diagonal line |
| Laminarity | Often `0.0` for simple diagonal recurrence |
| CORM | `0.0` if recurrent points lie on the main diagonal |

For recurrence, identical scanpaths do not necessarily produce `100`.

If the scanpath has \(N\) fixations and only diagonal self-matches are recurrent, then:

$$
\mathrm{REC} = \frac{100}{N}
$$

For example, with \(N = 4\):

$$
\mathrm{REC} = 25
$$

This is expected because the recurrence matrix has \(N \times N\) cells, and only \(N\) diagonal cells are recurrent.

---

## Human Group-vs-Human Group Evaluation

After dummy validation, the next stage is human group-vs-human group evaluation on real datasets.

For each dataset and each image, human scanpaths are split into two groups:

```text
prediction_part
groundtruth_part
```

The `prediction_part` contains human scanpaths that are treated as pseudo-predictions.

The `groundtruth_part` contains human scanpaths used as the reference group.

For each image, every scanpath in the prediction group is compared against every scanpath in the ground-truth group.

For example, if an image has six subjects:

```text
prediction_part:
s01, s02, s03

groundtruth_part:
s04, s05, s06
```

then the evaluation compares:

```text
s01 vs s04
s01 vs s05
s01 vs s06

s02 vs s04
s02 vs s05
s02 vs s06

s03 vs s04
s03 vs s05
s03 vs s06
```

This produces a distribution of human group-vs-human group metric values.

This distribution is important because it provides a human-level reference for interpreting model predictions.

---

## Model-vs-Human Evaluation

After human group-vs-human group evaluation, model-generated scanpaths can be compared against the same `groundtruth_part`.

For example:

```text
DeepGaze III + sampler -> predicted scanpaths
MD-SEM + sampler       -> predicted scanpaths
MD-EAM + sampler       -> predicted scanpaths
```

Each model-generated scanpath is evaluated against the human ground-truth group.

The final comparison should include:

```text
human group-vs-human group reference
model-vs-human performance
random baseline-vs-human performance
center baseline-vs-human performance
```

This helps answer whether a model is close to human variability or far below human-level scanpath agreement.

---

## Interpretation Guidelines

Different metrics measure different aspects of scanpath similarity.

Distance or error metrics should generally decrease when predictions improve:

```text
mean_fixation_error
final_fixation_error
mean_saccade_amplitude_error
mean_saccade_angle_error
mean_duration_error
dtw
frechet
hausdorff
levenshtein
eyenalysis
tde
scaled_tde
```

Similarity metrics should generally increase when predictions improve:

```text
duration_correlation
multimatch_shape
multimatch_direction
multimatch_length
multimatch_position
multimatch_duration
scanmatch
needleman_wunsch
aoi_transition_similarity
sequence_score
mannan_distance
```

Descriptive metrics do not have a universal better/worse direction:

```text
number_of_fixations
aoi_transition_count
recurrence
determinism
laminarity
corm
```

These should be compared against human distributions instead of interpreted as direct accuracy scores.

A model should not be judged using a single metric. For example:

- A model can have good spatial coverage but poor fixation order.
- A model can have good fixation positions but unrealistic saccade directions.
- A model can have realistic sequence structure but unrealistic fixation durations.

Therefore, results should be reported by metric family.

---

## Current Status

This metric layer has been validated using dummy `same`, `good`, and `bad` prediction cases.

The next stage is human group-vs-human group evaluation on real datasets such as UEyes and MASSVIS.

---

## References

This section lists the main references for the scanpath metrics used in this benchmark.

### General scanpath comparison

These papers are useful for justifying the use of multiple complementary scanpath metrics.

```bibtex
@article{anderson2015comparison,
  title={A comparison of scanpath comparison methods},
  author={Anderson, Nicola C. and Anderson, Fraser and Kingstone, Alan and Bischof, Walter F.},
  journal={Behavior Research Methods},
  volume={47},
  pages={1377--1392},
  year={2015},
  doi={10.3758/s13428-014-0550-3}
}

@article{fahimi2021metrics,
  title={On metrics for measuring scanpath similarity},
  author={Fahimi, Ramin and Bruce, Neil D. B.},
  journal={Behavior Research Methods},
  volume={53},
  pages={609--628},
  year={2021},
  doi={10.3758/s13428-020-01441-0}
}
```

### MultiMatch

These references describe the original MultiMatch method and the Python implementation used in this project.

```bibtex
@inproceedings{jarodzka2010vector,
  title={A vector-based, multidimensional scanpath similarity measure},
  author={Jarodzka, Halszka and Holmqvist, Kenneth and Nystr{\\o}m, Marcus},
  booktitle={Proceedings of the Symposium on Eye-Tracking Research and Applications},
  pages={211--218},
  year={2010},
  doi={10.1145/1743666.1743718}
}

@article{dewhurst2012multimatch,
  title={It depends on how you look at it: Scanpath comparison in multiple dimensions with MultiMatch, a vector-based approach},
  author={Dewhurst, Richard and Nystr{\\o}m, Marcus and Jarodzka, Halszka and Foulsham, Tom and Johansson, Roger and Holmqvist, Kenneth},
  journal={Behavior Research Methods},
  volume={44},
  number={4},
  pages={1079--1100},
  year={2012},
  doi={10.3758/s13428-012-0212-2}
}

@article{wagner2019multimatch,
  title={multimatch-gaze: The MultiMatch algorithm for gaze path comparison in Python},
  author={Wagner, Adina S. and others},
  journal={Journal of Open Source Software},
  volume={4},
  number={40},
  pages={1525},
  year={2019},
  doi={10.21105/joss.01525}
}
```

### Alignment metrics

These references support DTW and discrete Fréchet distance.

```bibtex
@inproceedings{berndt1994dtw,
  title={Using Dynamic Time Warping to Find Patterns in Time Series},
  author={Berndt, Donald J. and Clifford, James},
  booktitle={AAAI Workshop on Knowledge Discovery in Databases},
  pages={359--370},
  year={1994}
}

@techreport{eiter1994frechet,
  title={Computing Discrete Fr{\\'e}chet Distance},
  author={Eiter, Thomas and Mannila, Heikki},
  institution={Technical University of Vienna},
  year={1994}
}
@article{mannan1995automatic,
  title={Automatic control of saccadic eye movements made in visual inspection of briefly presented 2-D images},
  author={Mannan, S. K. and Ruddock, K. H. and Wooding, D. S.},
  journal={Spatial Vision},
  volume={9},
  number={3},
  pages={363--386},
  year={1995}
}

@article{mathot2012simple,
  title={A simple way to estimate similarity between pairs of eye movement sequences},
  author={Math{\^o}t, Sebastiaan and Cristino, Filipe and Gilchrist, Iain D. and Theeuwes, Jan},
  journal={Journal of Eye Movement Research},
  volume={5},
  number={1},
  pages={1--15},
  year={2012},
  doi={10.16910/jemr.5.1.4}
}
```

### Symbolic sequence metrics

These references support ScanMatch, Needleman-Wunsch alignment, and Levenshtein distance.

```bibtex
@article{cristino2010scanmatch,
  title={ScanMatch: A novel method for comparing fixation sequences},
  author={Cristino, Filipe and Math{\\^o}t, Sebastiaan and Theeuwes, Jan and Gilchrist, Iain D.},
  journal={Behavior Research Methods},
  volume={42},
  number={3},
  pages={692--700},
  year={2010},
  doi={10.3758/BRM.42.3.692}
}

@article{needleman1970general,
  title={A general method applicable to the search for similarities in the amino acid sequence of two proteins},
  author={Needleman, Saul B. and Wunsch, Christian D.},
  journal={Journal of Molecular Biology},
  volume={48},
  number={3},
  pages={443--453},
  year={1970},
  doi={10.1016/0022-2836(70)90057-4}
}

@article{levenshtein1966binary,
  title={Binary codes capable of correcting deletions, insertions, and reversals},
  author={Levenshtein, Vladimir I.},
  journal={Soviet Physics Doklady},
  volume={10},
  number={8},
  pages={707--710},
  year={1966}
}
```

### Recurrence metrics

These references support recurrence quantification analysis and recurrence-based scanpath comparison.

```bibtex
@article{anderson2013rqa,
  title={Recurrence quantification analysis of eye movements},
  author={Anderson, Nicola C. and Bischof, Walter F.},
  journal={Behavior Research Methods},
  volume={45},
  pages={842--856},
  year={2013},
  doi={10.3758/s13428-012-0299-5}
}

@article{marwan2007recurrence,
  title={Recurrence plots for the analysis of complex systems},
  author={Marwan, Norbert and Romano, M. Carmen and Thiel, Marco and Kurths, J{\\u}rgen},
  journal={Physics Reports},
  volume={438},
  number={5--6},
  pages={237--329},
  year={2007},
  doi={10.1016/j.physrep.2006.11.001}
}
```

### Temporal embedding metrics

These references support time-delay embedding and scanpath prediction metrics based on temporal embedding.

```bibtex
@incollection{takens1981detecting,
  title={Detecting strange attractors in turbulence},
  author={Takens, Floris},
  booktitle={Dynamical Systems and Turbulence, Warwick 1980},
  pages={366--381},
  year={1981},
  publisher={Springer}
}

@inproceedings{wang2011simulating,
  title={Simulating human saccadic scanpaths on natural images},
  author={Wang, Wei and Chen, Chen and Wang, Yizhou and Jiang, Tieniu and Fang, Fang and Yao, Yuan},
  booktitle={Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition},
  pages={441--448},
  year={2011},
  doi={10.1109/CVPR.2011.5995563}
}
```

### Notes

Some metrics in this benchmark are implemented as auxiliary or simplified variants.

For example:

- `mean_fixation_error`, `final_fixation_error`, `mean_saccade_amplitude_error`, and `mean_saccade_angle_error` are simple geometric auxiliary metrics.
- `scanmatch` is currently a Python ScanMatch-style implementation based on grid-AOI conversion and Needleman-Wunsch alignment, not the official MATLAB ScanMatch toolbox.
- `mannan_distance` is implemented as a Mannan-style spatial similarity relative to a random baseline.
- `number_of_fixations` and `aoi_transition_count` are descriptive scanpath statistics, not prediction-vs-human similarity metrics.
