from datetime import datetime

from internetmetr.domain.entities.network_snapshot import NetworkSnapshot
from internetmetr.domain.ports.network_info_port import NetworkInfoPort


class GetNetworkSnapshotUseCase:
    def __init__(self, network_info: NetworkInfoPort) -> None:
        self._network_info = network_info

    def execute(self) -> NetworkSnapshot:
        return NetworkSnapshot(
            created_at=datetime.now(),
            interfaces=self._network_info.list_interfaces(),
            hostname=self._network_info.get_hostname(),
            local_ipv4=self._network_info.get_primary_local_ipv4(),
            public_ip=self._network_info.get_public_ip(),
        )
