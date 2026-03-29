import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from internetmetr.composition import build_main_view_model
from internetmetr.presentation.qt.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    icon_path = Path(__file__).resolve().parent / "presentation" / "qt" / "assets" / "app_icon.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    try:
        view_model = build_main_view_model()
    except NotImplementedError as exc:
        QMessageBox.critical(None, "Platform Not Supported", str(exc))
        raise SystemExit(1) from exc
    except RuntimeError as exc:
        QMessageBox.critical(None, "Startup Error", str(exc))
        raise SystemExit(1) from exc

    window = MainWindow(view_model)
    window.show()

    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
