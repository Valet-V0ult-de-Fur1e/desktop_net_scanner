from internetmetr.application.use_cases.get_network_snapshot import GetNetworkSnapshotUseCase
from internetmetr.application.use_cases.run_speed_test import RunSpeedTestUseCase
from internetmetr.infrastructure.adapters.speed.speedtest_cli_adapter import SpeedtestCliAdapter
from internetmetr.infrastructure.platform_factory import build_network_adapter
from internetmetr.presentation.qt.viewmodels.main_view_model import MainViewModel


def build_main_view_model() -> MainViewModel:
    network_adapter = build_network_adapter()
    speed_adapter = SpeedtestCliAdapter()

    get_network_snapshot_use_case = GetNetworkSnapshotUseCase(network_adapter)
    run_speed_test_use_case = RunSpeedTestUseCase(speed_adapter)

    return MainViewModel(get_network_snapshot_use_case, run_speed_test_use_case)
