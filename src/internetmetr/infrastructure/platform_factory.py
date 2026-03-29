import sys

from internetmetr.domain.ports.network_info_port import NetworkInfoPort
from internetmetr.infrastructure.adapters.platform.linux_network_adapter import LinuxNetworkInfoAdapter
from internetmetr.infrastructure.adapters.platform.macos_network_adapter import MacOsNetworkInfoAdapter
from internetmetr.infrastructure.adapters.platform.windows_network_adapter import WindowsNetworkInfoAdapter


def build_network_adapter() -> NetworkInfoPort:
    if sys.platform == "win32":
        return WindowsNetworkInfoAdapter()
    if sys.platform.startswith("linux"):
        return LinuxNetworkInfoAdapter()
    if sys.platform == "darwin":
        return MacOsNetworkInfoAdapter()

    raise RuntimeError(f"Unsupported platform: {sys.platform}")
