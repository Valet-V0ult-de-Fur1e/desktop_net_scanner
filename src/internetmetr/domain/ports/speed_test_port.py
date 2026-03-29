from collections.abc import Callable
from typing import Protocol

from internetmetr.domain.entities.speed_test_result import SpeedTestResult


class SpeedTestPort(Protocol):
    def run_test(self, trace: Callable[[str], None] | None = None) -> SpeedTestResult:
        ...
