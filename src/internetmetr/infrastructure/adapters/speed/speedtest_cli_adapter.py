from collections.abc import Callable

import speedtest

from internetmetr.domain.entities.speed_test_result import SpeedTestResult
from internetmetr.domain.ports.speed_test_port import SpeedTestPort


class SpeedtestCliAdapter(SpeedTestPort):
    def run_test(self, trace: Callable[[str], None] | None = None) -> SpeedTestResult:
        if trace:
            trace("Initializing speed test client")
        client = speedtest.Speedtest()

        if trace:
            trace("Selecting the nearest test server")
        client.get_best_server()

        if trace:
            trace("Measuring download throughput")
        download_bps = client.download()

        if trace:
            trace("Measuring upload throughput")
        upload_bps = client.upload(pre_allocate=False)

        if trace:
            trace("Collecting latency and final report")
        ping_ms = float(client.results.ping or 0.0)
        server_name = str(client.results.server.get("name", "Unknown"))

        download_mbps = max(0.0, float(download_bps) / 1_000_000)
        upload_mbps = max(0.0, float(upload_bps) / 1_000_000)

        return SpeedTestResult(
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            ping_ms=ping_ms,
            server_name=server_name,
        )
