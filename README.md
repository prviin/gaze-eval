# gaze-eval

`gaze-eval` is a Python package for evaluating gaze prediction models.

The package is designed to support two main evaluation tasks:

- scanpath prediction evaluation
- saliency-map prediction evaluation

The current version focuses on scanpath metrics and dummy validation data. Saliency-map metrics and dataset loaders will be added later.

---

## Current Status

Implemented:

- scanpath metric functions
- scanpath metric registry
- dummy scanpath data
- basic validation tests
- scanpath metric documentation

Planned:

- saliency-map metrics
- saliency-map evaluation pipeline
- dataset loaders
- human group-vs-human group evaluation


---

## Installation

For local development, clone the repository and install it in editable mode:

```bash
git clone https://github.com/prviin/gaze-eval.git
cd gaze-eval
pip install -e ".[dev]"
```

If editable installation is not available in your environment, you can still run the package using:

```bash
PYTHONPATH=src python -m pytest
```

---

## Package Structure

```text
gaze-eval/
├── src/
│   └── gaze_eval/
│       └── scanpath/
│           ├── metrics.py
│           ├── registry.py
│           ├── evaluate.py
│           └── aggregate.py
├── tests/
│   └── data/
│       └── debug/
│           ├── human_scanpaths.csv
│           ├── pred_same.csv
│           ├── pred_good.csv
│           └── pred_bad.csv
├── docs/
│   └── scanpath_metrics.md
└── examples/
```

---

## Scanpath Data Format

Human scanpaths should use the following columns:

```text
image_id, subject_id, fixation_index, x, y, duration
```

Predicted scanpaths should use the following columns:

```text
image_id, prediction_id, model, sampler, fixation_index, x, y, duration
```

Coordinates should be normalized:

```text
x in [0, 1]
y in [0, 1]
```

Durations should be reported in milliseconds.

If duration is unavailable, use:

```text
duration = -1
```

---

## Example Usage

```python
import pandas as pd

from gaze_eval.scanpath.metrics import mean_fixation_error, dtw_distance

human = pd.read_csv("tests/data/debug/human_scanpaths.csv")
pred = pd.read_csv("tests/data/debug/pred_good.csv")

human_s01 = human[human["subject_id"] == "s01"]

mfe = mean_fixation_error(pred, human_s01)
dtw = dtw_distance(pred, human_s01)

print("Mean fixation error:", mfe)
print("DTW distance:", dtw)
```

---

## Implemented Scanpath Metric Groups

The current scanpath module includes metrics from the following groups:

- point-wise geometric metrics
- temporal metrics
- alignment metrics
- MultiMatch metrics
- symbolic / grid-AOI metrics
- spatial set-based metrics
- recurrence-based metrics
- temporal-embedding metrics
- descriptive scanpath statistics

See the full documentation:

```text
docs/scanpath_metrics.md
```

---

## Dummy Validation Data

The repository includes small dummy scanpath files for testing:

```text
tests/data/debug/human_scanpaths.csv
tests/data/debug/pred_same.csv
tests/data/debug/pred_good.csv
tests/data/debug/pred_bad.csv
```

The dummy cases are designed so that:

```text
pred_same = identical to one human scanpath
pred_good = slightly shifted scanpath
pred_bad  = clearly different scanpath
```

For distance/error metrics, the expected behavior is:

```text
same < good < bad
```

For similarity metrics, the expected behavior is:

```text
same > good > bad
```

---

## Running Tests

Run:

```bash
python -m pytest
```

If the package is not installed in the current environment, run:

```bash
PYTHONPATH=src python -m pytest
```

---

## Development Notes

During development, install with:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
python -m pytest
```

Check code style:

```bash
ruff check .
```

---

## Roadmap

Short-term:

- add `evaluate_scanpaths`
- add aggregation utilities
- add example script for dummy scanpath evaluation
- improve tests for all metric families

Medium-term:

- add saliency-map metrics
- add saliency-map evaluation pipeline
- add fixation-map utilities
- add dataset loaders for common benchmarks

Long-term:

- support human group-vs-human group evaluation
- support model-vs-human evaluation
- provide benchmark scripts for scanpath and saliency prediction models

---

## License


