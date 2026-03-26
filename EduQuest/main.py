import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    qss_path = Path(__file__).parent / "styles" / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
