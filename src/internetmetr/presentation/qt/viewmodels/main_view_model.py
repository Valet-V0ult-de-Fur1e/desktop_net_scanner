from dataclasses import dataclass
from collections.abc import Callable

from internetmetr.application.use_cases.get_network_snapshot import GetNetworkSnapshotUseCase
from internetmetr.application.use_cases.run_speed_test import RunSpeedTestUseCase
from internetmetr.domain.entities.network_interface import NetworkInterface
from internetmetr.domain.entities.speed_test_result import SpeedTestResult


@dataclass(frozen=True)
class MainScreenState:
    hostname: str
    local_ip: str
    public_ip: str
    interfaces: list[NetworkInterface]


class MainViewModel:
    def __init__(
        self,
        get_network_snapshot: GetNetworkSnapshotUseCase,
        run_speed_test: RunSpeedTestUseCase,
    ) -> None:
        self._get_network_snapshot = get_network_snapshot
        self._run_speed_test = run_speed_test

    def load_network_state(self) -> MainScreenState:
        snapshot = self._get_network_snapshot.execute()
        return MainScreenState(
            hostname=snapshot.hostname,
            local_ip=snapshot.local_ipv4 or "-",
            public_ip=snapshot.public_ip or "-",
            interfaces=snapshot.interfaces,
        )

    def run_speed_test(self, trace: Callable[[str], None] | None = None) -> SpeedTestResult:
        return self._run_speed_test.execute(trace=trace)

    def evaluate_quality_score(
        self, download_mbps: float, upload_mbps: float, ping_ms: float
    ) -> tuple[int, str]:
        download_score = min(4.0, max(0.0, download_mbps / 25.0 * 4.0))
        upload_score = min(3.0, max(0.0, upload_mbps / 10.0 * 3.0))
        latency_score = min(3.0, max(0.0, (120.0 - ping_ms) / 120.0 * 3.0))

        total = round(download_score + upload_score + latency_score)
        bounded = min(10, max(1, int(total)))

        if bounded >= 9:
            label = "Excellent"
        elif bounded >= 7:
            label = "Good"
        elif bounded >= 5:
            label = "Average"
        elif bounded >= 3:
            label = "Poor"
        else:
            label = "Very Poor"

        return bounded, label
