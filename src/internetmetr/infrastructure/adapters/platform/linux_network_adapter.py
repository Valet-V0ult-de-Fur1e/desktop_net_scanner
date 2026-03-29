from internetmetr.domain.entities.network_interface import NetworkInterface
from internetmetr.domain.ports.network_info_port import NetworkInfoPort


class LinuxNetworkInfoAdapter(NetworkInfoPort):
    def list_interfaces(self) -> list[NetworkInterface]:
        raise NotImplementedError("Linux adapter is not implemented yet")

    def get_hostname(self) -> str:
        raise NotImplementedError("Linux adapter is not implemented yet")

    def get_primary_local_ipv4(self) -> str | None:
        raise NotImplementedError("Linux adapter is not implemented yet")

    def get_public_ip(self) -> str | None:
        raise NotImplementedError("Linux adapter is not implemented yet")
