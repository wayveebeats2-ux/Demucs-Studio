"""Launch the modern Demucs Studio interface."""
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))

import shared
shared.InitializeFolder()

from PySide6.QtWidgets import QApplication
from ui.main_window import StudioWindow
from ui.controller import StudioController


def main():
    app=QApplication.instance() or QApplication(sys.argv)
    window=StudioWindow(); controller=StudioController(window); window.attach_controller(controller)
    window.show(); controller.initialize()
    return app.exec()

if __name__=="__main__": raise SystemExit(main())
