"""Launch the experimental Demucs Studio interface without replacing legacy GuiMain.py."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from PySide6.QtWidgets import QApplication
from ui.main_window import StudioWindow


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = StudioWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
