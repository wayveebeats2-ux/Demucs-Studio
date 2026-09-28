from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QListWidget, QMainWindow, QProgressBar, QPushButton, QVBoxLayout, QWidget)

from ui.drop_zone import DropZone
from ui.theme import DARK_STYLESHEET


class StudioWindow(QMainWindow):
    """Phase-one Demucs Studio shell. Separation wiring intentionally follows later."""
    def __init__(self, device_text="Detecting device…"):
        super().__init__()
        self.setWindowTitle("Demucs Studio")
        self.resize(1080, 720)
        self.setMinimumSize(820, 580)
        self.setStyleSheet(DARK_STYLESHEET)
        self._build(device_text)

    def _build(self, device_text):
        root = QWidget(); outer = QVBoxLayout(root); outer.setContentsMargins(22,22,22,22); outer.setSpacing(14)
        header = QFrame(); header.setObjectName("header"); h = QHBoxLayout(header)
        brand = QLabel("DEMUX STUDIO"); brand.setObjectName("brand")
        self.device = QLabel(device_text); self.device.setObjectName("accent")
        h.addWidget(brand); h.addStretch(); h.addWidget(self.device); outer.addWidget(header)

        self.drop = DropZone(); self.drop.filesDropped.connect(self.add_files); outer.addWidget(self.drop)

        controls = QFrame(); controls.setObjectName("panel"); c = QHBoxLayout(controls)
        self.preset = QComboBox(); self.preset.addItems(["4 Stem • Vocals / Drums / Bass / Other", "Vocals • 2 Stem", "6 Stem"])
        self.model = QComboBox(); self.model.addItems(["htdemucs • Recommended", "htdemucs_ft • Higher quality", "htdemucs_6s • 6 stem"])
        add = QPushButton("Add Tracks"); add.clicked.connect(self.pick_files)
        self.separate = QPushButton("SEPARATE"); self.separate.setObjectName("primary"); self.separate.setEnabled(False)
        c.addWidget(QLabel("Preset")); c.addWidget(self.preset,2); c.addWidget(QLabel("Model")); c.addWidget(self.model,2); c.addWidget(add); c.addWidget(self.separate)
        outer.addWidget(controls)

        queue_panel = QFrame(); queue_panel.setObjectName("panel"); q = QVBoxLayout(queue_panel)
        title = QLabel("QUEUE"); title.setObjectName("accent"); q.addWidget(title)
        self.queue = QListWidget(); q.addWidget(self.queue,1)
        self.progress = QProgressBar(); self.progress.setRange(0,100); self.progress.setValue(0); q.addWidget(self.progress)
        outer.addWidget(queue_panel,1)
        footer = QLabel("Phase 1 • Modern interface shell • Existing Demucs backend remains untouched")
        footer.setObjectName("muted"); outer.addWidget(footer)
        self.setCentralWidget(root)

    def pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Add audio tracks", "", "Audio files (*.*)")
        self.add_files(files)

    def add_files(self, files):
        existing = {self.queue.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.queue.count())}
        for file in files:
            if file not in existing:
                self.queue.addItem(Path(file).name)
                self.queue.item(self.queue.count()-1).setData(Qt.ItemDataRole.UserRole, file)
                existing.add(file)
        self.separate.setEnabled(self.queue.count() > 0)
