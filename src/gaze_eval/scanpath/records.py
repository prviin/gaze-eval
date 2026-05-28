from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class Fixation:
    fixation_index: int
    x: float
    y: float
    duration: float
    timestamp: float | None = None


@dataclass(frozen=True)
class ScanpathRecord:
    schema_version: str
    source: Literal["human", "prediction"]
    dataset: str
    image_id: str
    trial_id: str
    scanpath: list[Fixation]

    subject_id: str | None = None
    prediction_id: str | None = None
    model: str | None = None
    sampler: str | None = None

    split: str | None = None
    task_id: str | None = None
    condition: str | None = None
    session_id: str | None = None
    run_id: str | None = None

    stimulus: dict[str, Any] = field(default_factory=dict)
    coordinate_system: dict[str, Any] = field(default_factory=dict)
    time_unit: str = "ms"
    duration_unit: str = "ms"
    metadata: dict[str, Any] = field(default_factory=dict)
