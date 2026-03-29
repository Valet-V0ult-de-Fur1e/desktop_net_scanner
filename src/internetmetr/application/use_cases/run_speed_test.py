from collections.abc import Callable

from internetmetr.domain.entities.speed_test_result import SpeedTestResult
from internetmetr.domain.ports.speed_test_port import SpeedTestPort


class RunSpeedTestUseCase:
    def __init__(self, speed_test: SpeedTestPort) -> None:
        self._speed_test = speed_test

    def execute(self, trace: Callable[[str], None] | None = None) -> SpeedTestResult:
        return self._speed_test.run_test(trace=trace)
