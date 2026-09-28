from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QListWidget, QMainWindow, QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget)

from ui.drop_zone import DropZone
from ui.theme import DARK_STYLESHEET


class StudioWindow(QMainWindow):
    deviceChanged = Signal(str); statusChanged = Signal(str); backendReady = Signal()
    busyChanged = Signal(bool); modelProgress = Signal(float); trackProgress = Signal(int, float)
    trackStarted = Signal(int, str); trackStatus = Signal(int, int); trackFinished = Signal(int, int)
    allFinished = Signal(); errorRaised = Signal(str, str)

    def __init__(self):
        super().__init__(); self.controller = None
        self.setWindowTitle("Demucs Studio"); self.resize(1080,720); self.setMinimumSize(820,580)
        self.setStyleSheet(DARK_STYLESHEET); self._build(); self._connect_signals()

    def attach_controller(self, controller): self.controller = controller

    def _build(self):
        root=QWidget(); outer=QVBoxLayout(root); outer.setContentsMargins(22,22,22,22); outer.setSpacing(14)
        header=QFrame(); header.setObjectName("header"); h=QHBoxLayout(header)
        brand=QLabel("DEMUX STUDIO"); brand.setObjectName("brand"); self.device=QLabel("Starting backend…"); self.device.setObjectName("accent")
        h.addWidget(brand); h.addStretch(); h.addWidget(self.device); outer.addWidget(header)
        self.drop=DropZone(); self.drop.filesDropped.connect(self.add_files); outer.addWidget(self.drop)
        controls=QFrame(); controls.setObjectName("panel"); c=QHBoxLayout(controls)
        self.preset=QComboBox(); self.preset.addItems(["4 Stem • Vocals / Drums / Bass / Other","Vocals • 2 Stem","6 Stem"])
        self.model=QComboBox(); self.model.addItem("htdemucs • Recommended","htdemucs"); self.model.addItem("htdemucs_ft • Higher quality","htdemucs_ft"); self.model.addItem("htdemucs_6s • 6 stem","htdemucs_6s")
        add=QPushButton("Add Tracks"); add.clicked.connect(self.pick_files); self.separate=QPushButton("SEPARATE"); self.separate.setObjectName("primary"); self.separate.setEnabled(False); self.separate.clicked.connect(self.start)
        c.addWidget(QLabel("Preset")); c.addWidget(self.preset,2); c.addWidget(QLabel("Model")); c.addWidget(self.model,2); c.addWidget(add); c.addWidget(self.separate); outer.addWidget(controls)
        panel=QFrame(); panel.setObjectName("panel"); q=QVBoxLayout(panel); title=QLabel("QUEUE"); title.setObjectName("accent"); q.addWidget(title)
        self.queue=QListWidget(); q.addWidget(self.queue,1); self.progress=QProgressBar(); self.progress.setRange(0,100); q.addWidget(self.progress); outer.addWidget(panel,1)
        self.status=QLabel("Initializing Demucs…"); self.status.setObjectName("muted"); outer.addWidget(self.status); self.setCentralWidget(root)

    def _connect_signals(self):
        self.deviceChanged.connect(self.device.setText); self.statusChanged.connect(self.status.setText)
        self.backendReady.connect(self._refresh_enabled); self.busyChanged.connect(lambda busy: self.separate.setEnabled(not busy and self.queue.count()>0))
        self.trackProgress.connect(self._progress); self.trackStarted.connect(lambda row,name: self._set_row(row,f"⏳ {name}"))
        self.trackFinished.connect(self._finished); self.allFinished.connect(lambda: self.progress.setValue(100)); self.errorRaised.connect(self._error)

    def pick_files(self):
        files,_=QFileDialog.getOpenFileNames(self,"Add audio tracks","","Audio files (*.*)"); self.add_files(files)
    def add_files(self,files):
        existing={self.queue.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.queue.count())}
        for file in files:
            if file not in existing:
                self.queue.addItem(Path(file).name); self.queue.item(self.queue.count()-1).setData(Qt.ItemDataRole.UserRole,file); existing.add(file)
        self._refresh_enabled()
    def _refresh_enabled(self): self.separate.setEnabled(self.controller is not None and not self.controller.busy and self.queue.count()>0)
    def start(self):
        if not self.controller:return
        files=[self.queue.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.queue.count())]
        self.progress.setValue(0); self.controller.load_model_and_start(self.model.currentData(),files)
    def _progress(self,row,value):
        self.progress.setValue(int(value*100)); name=Path(self.queue.item(row).data(Qt.ItemDataRole.UserRole)).name; self._set_row(row,f"⏳ {name}  •  {int(value*100)}%")
    def _finished(self,row,status):
        name=Path(self.queue.item(row).data(Qt.ItemDataRole.UserRole)).name; self._set_row(row,("✓ " if status==5 else "✕ ")+name)
    def _set_row(self,row,text):
        if 0<=row<self.queue.count(): self.queue.item(row).setText(text)
    def _error(self,title,message): QMessageBox.critical(self,title,message)
