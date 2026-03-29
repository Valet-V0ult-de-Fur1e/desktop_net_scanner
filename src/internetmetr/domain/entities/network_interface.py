from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkInterface:
    name: str
    is_up: bool
    mac_address: str
    ipv4_addresses: list[str]
    ipv6_addresses: list[str]
    speed_mbps: int | None
    mtu: int | None
