# Datasets

This package will support dataset loaders that convert public eye-tracking datasets into the standard `gaze-eval` scanpath format.

## Standard scanpath format

```text
dataset, image_id, subject_id, fixation_index, x, y, duration
```
Coordinates must be normalized to ```[0, 1]```.

Durations should be in milliseconds. If duration is unavailable, ```use -1```.

#TODO: next step is to download/inspect the MASSVIS/UMSS dataset structure and write the first real loader: