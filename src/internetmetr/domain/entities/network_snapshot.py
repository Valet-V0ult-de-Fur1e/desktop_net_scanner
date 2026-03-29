from dataclasses import dataclass
from datetime import datetime

from internetmetr.domain.entities.network_interface import NetworkInterface


@dataclass(frozen=True)
class NetworkSnapshot:
    created_at: datetime
    interfaces: list[NetworkInterface]
    hostname: str
    local_ipv4: str | None
    public_ip: str | None
