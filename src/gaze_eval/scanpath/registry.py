from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd


@dataclass(frozen=True)
class ScanpathMetric:
    name: str
    function: Callable[[pd.DataFrame, pd.DataFrame], float]
    category: str
    direction: str
    description: str
    requires_duration: bool = False
