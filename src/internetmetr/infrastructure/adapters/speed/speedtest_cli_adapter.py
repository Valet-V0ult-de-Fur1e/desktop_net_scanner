from collections.abc import Callable
import os
import sys
import time

import requests

from internetmetr.domain.entities.speed_test_result import SpeedTestResult
from internetmetr.domain.ports.speed_test_port import SpeedTestPort


class SpeedtestCliAdapter(SpeedTestPort):
    def run_test(self, trace: Callable[[str], None] | None = None) -> SpeedTestResult:
        try:
            return self._run_primary_speedtest(trace)
        except Exception as exc:  # noqa: BLE001
            if trace:
                trace(f"Primary speed provider failed: {exc}")
                trace("Switching to fallback HTTP probes")

            return self._run_fallback_http(trace)

    def _run_primary_speedtest(self, trace: Callable[[str], None] | None = None) -> SpeedTestResult:
        self._ensure_standard_streams_for_speedtest()
        import speedtest

        if trace:
            trace("Initializing speed test client")
        client = speedtest.Speedtest(secure=True)

        if trace:
            trace("Selecting the nearest test server")
        client.get_best_server()

        if trace:
            trace("Measuring download throughput")
        download_bps = client.download(threads=4)

        if trace:
            trace("Measuring upload throughput")
        upload_bps = client.upload(pre_allocate=False, threads=2)

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

    def _ensure_standard_streams_for_speedtest(self) -> None:
        # In PyInstaller --windowed builds, stdout/stderr can be None.
        # speedtest-cli touches these streams during import/init.
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w")

    def _run_fallback_http(self, trace: Callable[[str], None] | None = None) -> SpeedTestResult:
        if trace:
            trace("Fallback: measuring latency")
        ping_ms = self._measure_ping_ms()

        if trace:
            trace("Fallback: measuring download throughput")
        download_mbps = self._measure_download_mbps()

        if trace:
            trace("Fallback: measuring upload throughput")
        upload_mbps = self._measure_upload_mbps()

        if trace:
            trace("Fallback speed test completed")

        return SpeedTestResult(
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            ping_ms=ping_ms,
            server_name="Fallback HTTP Probe",
        )

    def _measure_ping_ms(self) -> float:
        latencies: list[float] = []
        for _ in range(3):
            start = time.perf_counter()
            requests.get("https://speed.cloudflare.com/cdn-cgi/trace", timeout=5)
            end = time.perf_counter()
            latencies.append((end - start) * 1000.0)

        return sum(latencies) / len(latencies)

    def _measure_download_mbps(self) -> float:
        bytes_to_read = 12_000_000
        url = f"https://speed.cloudflare.com/__down?bytes={bytes_to_read}"

        start = time.perf_counter()
        bytes_read = 0
        with requests.get(url, stream=True, timeout=20) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                bytes_read += len(chunk)
        elapsed = max(time.perf_counter() - start, 1e-6)

        return max(0.0, (bytes_read * 8) / elapsed / 1_000_000)

    def _measure_upload_mbps(self) -> float:
        payload = os.urandom(4_000_000)
        url = "https://speed.cloudflare.com/__up"

        start = time.perf_counter()
        response = requests.post(url, data=payload, timeout=20)
        response.raise_for_status()
        elapsed = max(time.perf_counter() - start, 1e-6)

        return max(0.0, (len(payload) * 8) / elapsed / 1_000_000)
