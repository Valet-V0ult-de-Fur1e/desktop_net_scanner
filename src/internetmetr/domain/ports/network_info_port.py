from typing import Protocol

from internetmetr.domain.entities.network_interface import NetworkInterface


class NetworkInfoPort(Protocol):
    def list_interfaces(self) -> list[NetworkInterface]:
        ...

    def get_hostname(self) -> str:
        ...

    def get_primary_local_ipv4(self) -> str | None:
        ...

    def get_public_ip(self) -> str | None:
        ...
