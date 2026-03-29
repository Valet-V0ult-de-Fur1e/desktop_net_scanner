import socket

import psutil
import requests

from internetmetr.domain.entities.network_interface import NetworkInterface
from internetmetr.domain.ports.network_info_port import NetworkInfoPort


class WindowsNetworkInfoAdapter(NetworkInfoPort):
    def list_interfaces(self) -> list[NetworkInterface]:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        interfaces: list[NetworkInterface] = []
        for interface_name, addr_list in addrs.items():
            stat = stats.get(interface_name)
            ipv4_addresses: list[str] = []
            ipv6_addresses: list[str] = []
            mac_address = ""

            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    ipv4_addresses.append(addr.address)
                elif addr.family == socket.AF_INET6:
                    ipv6_addresses.append(addr.address.split("%")[0])
                elif getattr(psutil, "AF_LINK", None) == addr.family:
                    mac_address = addr.address

            interfaces.append(
                NetworkInterface(
                    name=interface_name,
                    is_up=bool(stat and stat.isup),
                    mac_address=mac_address,
                    ipv4_addresses=ipv4_addresses,
                    ipv6_addresses=ipv6_addresses,
                    speed_mbps=(stat.speed if stat and stat.speed > 0 else None),
                    mtu=(stat.mtu if stat else None),
                )
            )

        interfaces.sort(key=lambda item: item.name.lower())
        return interfaces

    def get_hostname(self) -> str:
        return socket.gethostname()

    def get_primary_local_ipv4(self) -> str | None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # UDP connect does not send packets but lets us ask OS for active route.
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        except OSError:
            return None
        finally:
            sock.close()

    def get_public_ip(self) -> str | None:
        try:
            response = requests.get("https://api.ipify.org", timeout=3)
            response.raise_for_status()
            return response.text.strip()
        except requests.RequestException:
            return None
