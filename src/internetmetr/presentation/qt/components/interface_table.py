from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem

from internetmetr.domain.entities.network_interface import NetworkInterface


class InterfaceTable(QTableWidget):
    HEADERS = ["Name", "Status", "IPv4", "IPv6", "MAC", "Speed (Mbps)", "MTU"]

    def __init__(self) -> None:
        super().__init__(0, len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.horizontalHeader().setStretchLastSection(True)

    def set_interfaces(self, interfaces: list[NetworkInterface]) -> None:
        self.setRowCount(len(interfaces))
        for row, item in enumerate(interfaces):
            self.setItem(row, 0, QTableWidgetItem(item.name))
            self.setItem(row, 1, QTableWidgetItem("UP" if item.is_up else "DOWN"))
            self.setItem(row, 2, QTableWidgetItem(", ".join(item.ipv4_addresses) or "-"))
            self.setItem(row, 3, QTableWidgetItem(", ".join(item.ipv6_addresses) or "-"))
            self.setItem(row, 4, QTableWidgetItem(item.mac_address or "-"))
            self.setItem(
                row,
                5,
                QTableWidgetItem(str(item.speed_mbps) if item.speed_mbps is not None else "-"),
            )
            self.setItem(
                row,
                6,
                QTableWidgetItem(str(item.mtu) if item.mtu is not None else "-"),
            )
