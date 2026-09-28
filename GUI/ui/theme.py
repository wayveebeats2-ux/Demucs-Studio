"""Demucs Studio visual system — dark production UI with violet accents."""
DARK_STYLESHEET=r"""
QMainWindow,QWidget { background:#0b0f16; color:#edf0f7; font-family:"Segoe UI","Inter",sans-serif; font-size:13px; }
QFrame#header,QFrame#panel,QFrame#dropZone,QFrame#deviceCard { background:#121824; border:1px solid #263044; border-radius:12px; }
QFrame#dropZone { background:#111724; border:1px dashed #7557d9; }
QFrame#dropZone[dragActive="true"] { border:2px solid #9b6cff; background:#18152b; }
QLabel#brand { font-size:27px; font-weight:800; letter-spacing:2px; color:#f6f7fb; }
QLabel#subtitle { color:#a9a1c8; font-size:10px; letter-spacing:2px; }
QLabel#section { color:#c6b5ff; font-size:13px; font-weight:700; letter-spacing:1px; }
QLabel#muted { color:#8791a5; }
QLabel#accent { color:#a77cff; font-weight:700; }
QLabel#success { color:#55db83; font-weight:600; }
QPushButton { background:#1a2230; border:1px solid #303b50; border-radius:8px; padding:8px 13px; color:#eef1f8; font-weight:600; }
QPushButton:hover { background:#242e40; border-color:#6955aa; }
QPushButton:disabled { color:#626c7d; background:#141a24; }
QPushButton#danger:hover { border-color:#e04e61; color:#ff7888; }
QPushButton#primary { background:#7d4cff; border:1px solid #9d75ff; color:white; padding:11px 24px; font-weight:800; }
QPushButton#primary:hover { background:#9167ff; }
QComboBox,QSpinBox,QDoubleSpinBox { background:#151c28; border:1px solid #303b50; border-radius:8px; padding:7px 9px; min-height:20px; }
QComboBox:hover,QSpinBox:hover,QDoubleSpinBox:hover { border-color:#7057b8; }
QListWidget { background:transparent; border:none; outline:none; }
QListWidget::item { background:#151c28; border:1px solid #263044; border-radius:9px; padding:12px; margin:3px 0; }
QListWidget::item:selected { background:#182746; border:1px solid #3569c8; }
QProgressBar { background:#171e2a; border:1px solid #263044; border-radius:5px; min-height:9px; max-height:9px; text-align:center; color:transparent; }
QProgressBar::chunk { background:#7d4cff; border-radius:4px; }
QScrollBar:vertical { background:#101620; width:8px; }
QScrollBar::handle:vertical { background:#354055; border-radius:4px; min-height:30px; }
"""
