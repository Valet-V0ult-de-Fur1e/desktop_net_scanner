from dataclasses import dataclass


@dataclass(frozen=True)
class SpeedTestResult:
    download_mbps: float
    upload_mbps: float
    ping_ms: float
    server_name: str
