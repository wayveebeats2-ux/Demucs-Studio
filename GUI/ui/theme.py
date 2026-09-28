"""Visual theme for the Demucs Studio interface."""

DARK_STYLESHEET = r"""
QMainWindow, QWidget {
    background: #0d1016;
    color: #e9edf5;
    font-family: "Segoe UI", "Inter", sans-serif;
}
QFrame#header, QFrame#panel, QFrame#dropZone {
    background: #141923;
    border: 1px solid #252d3b;
    border-radius: 14px;
}
QFrame#dropZone[dragActive="true"] { border: 2px solid #54d8ff; background: #121e29; }
QLabel#brand { font-size: 24px; font-weight: 700; letter-spacing: 2px; }
QLabel#muted { color: #8d98aa; }
QLabel#accent { color: #54d8ff; font-weight: 600; }
QPushButton {
    background: #1d2532; border: 1px solid #303b4d; border-radius: 9px;
    padding: 9px 14px; color: #e9edf5; font-weight: 600;
}
QPushButton:hover { background: #273244; }
QPushButton#primary { background: #54d8ff; color: #071017; border: none; padding: 12px 22px; }
QPushButton#primary:hover { background: #79e2ff; }
QComboBox {
    background: #171d28; border: 1px solid #303b4d; border-radius: 8px; padding: 8px 10px;
}
QListWidget {
    background: transparent; border: none; outline: none;
}
QListWidget::item { background: #171d28; border: 1px solid #252d3b; border-radius: 9px; padding: 10px; margin: 3px 0; }
QProgressBar { background: #171d28; border: 1px solid #252d3b; border-radius: 6px; height: 10px; text-align: center; }
QProgressBar::chunk { background: #54d8ff; border-radius: 5px; }
"""
