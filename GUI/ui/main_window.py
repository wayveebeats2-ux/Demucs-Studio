from pathlib import Path
from PySide6.QtCore import Qt,Signal
from PySide6.QtWidgets import (QComboBox,QDoubleSpinBox,QFileDialog,QFrame,QHBoxLayout,QLabel,QListWidget,QMainWindow,QMessageBox,QProgressBar,QPushButton,QSpinBox,QVBoxLayout,QWidget)
from ui.drop_zone import DropZone
from ui.stem_results import StemResults
from ui.theme import DARK_STYLESHEET

class StudioWindow(QMainWindow):
    deviceChanged=Signal(str); statusChanged=Signal(str); backendReady=Signal(); busyChanged=Signal(bool); modelProgress=Signal(float); trackProgress=Signal(int,float); trackStarted=Signal(int,str); trackStatus=Signal(int,int); trackFinished=Signal(int,int); allFinished=Signal(); errorRaised=Signal(str,str); resultsReady=Signal(int,str,list)
    def __init__(self):
        super().__init__(); self.controller=None; self.setWindowTitle("Demucs Studio"); self.resize(1120,780); self.setMinimumSize(840,620); self.setStyleSheet(DARK_STYLESHEET); self._build(); self._connect_signals()
    def attach_controller(self,c):self.controller=c
    def _build(self):
        root=QWidget(); o=QVBoxLayout(root); o.setContentsMargins(22,22,22,22); o.setSpacing(14)
        header=QFrame(); header.setObjectName("header"); h=QHBoxLayout(header); brand=QLabel("DEMUX STUDIO"); brand.setObjectName("brand"); self.device=QLabel("Starting backend…"); self.device.setObjectName("accent"); h.addWidget(brand); h.addStretch(); h.addWidget(self.device); o.addWidget(header)
        self.drop=DropZone(); self.drop.filesDropped.connect(self.add_files); o.addWidget(self.drop)
        controls=QFrame(); controls.setObjectName("panel"); c=QHBoxLayout(controls); self.preset=QComboBox(); self.preset.addItems(["4 Stem • Vocals / Drums / Bass / Other","Vocals • 2 Stem","6 Stem"]); self.model=QComboBox(); self.model.addItem("htdemucs • Recommended","htdemucs"); self.model.addItem("htdemucs_ft • Higher quality","htdemucs_ft"); self.model.addItem("htdemucs_6s • 6 stem","htdemucs_6s"); add=QPushButton("Add Tracks"); add.clicked.connect(self.pick_files); adv=QPushButton("Advanced"); adv.clicked.connect(self._toggle_advanced); self.separate=QPushButton("SEPARATE"); self.separate.setObjectName("primary"); self.separate.setEnabled(False); self.separate.clicked.connect(self.start); c.addWidget(self.preset,2); c.addWidget(self.model,2); c.addWidget(add); c.addWidget(adv); c.addWidget(self.separate); o.addWidget(controls)
        self.advanced=QFrame(); self.advanced.setObjectName("panel"); a=QHBoxLayout(self.advanced); self.segment=QDoubleSpinBox(); self.segment.setRange(.1,3600); self.segment.setValue(7.8); self.segment.setSuffix(" s"); self.overlap=QDoubleSpinBox(); self.overlap.setRange(0,.99); self.overlap.setSingleStep(.05); self.overlap.setValue(.25); self.shifts=QSpinBox(); self.shifts.setRange(1,20); self.shifts.setValue(1); self.gain=QDoubleSpinBox(); self.gain.setRange(-24,24); self.gain.setSuffix(" dB"); self.depth=QComboBox(); self.depth.addItem("24-bit WAV","PCM_24"); self.depth.addItem("16-bit WAV","PCM_16"); self.depth.addItem("32-bit float WAV","FLOAT");
        for label,w in [("Segment",self.segment),("Overlap",self.overlap),("Shifts",self.shifts),("Input gain",self.gain),("Output",self.depth)]:a.addWidget(QLabel(label));a.addWidget(w)
        self.advanced.hide(); o.addWidget(self.advanced)
        body=QHBoxLayout(); queue_panel=QFrame(); queue_panel.setObjectName("panel"); q=QVBoxLayout(queue_panel); title=QLabel("QUEUE"); title.setObjectName("accent"); q.addWidget(title); self.queue=QListWidget(); q.addWidget(self.queue,1); self.progress=QProgressBar(); self.progress.setRange(0,100); q.addWidget(self.progress); body.addWidget(queue_panel,3); self.results=StemResults(); body.addWidget(self.results,2); o.addLayout(body,1); self.status=QLabel("Initializing Demucs…"); self.status.setObjectName("muted"); o.addWidget(self.status); self.setCentralWidget(root)
    def _connect_signals(self):
        self.deviceChanged.connect(self.device.setText); self.statusChanged.connect(self.status.setText); self.backendReady.connect(self._refresh_enabled); self.busyChanged.connect(lambda b:self.separate.setEnabled(not b and self.queue.count()>0)); self.trackProgress.connect(self._progress); self.trackStarted.connect(lambda r,n:self._set_row(r,f"⏳ {n}")); self.trackFinished.connect(self._finished); self.resultsReady.connect(self.results.show_results); self.allFinished.connect(lambda:self.progress.setValue(100)); self.errorRaised.connect(lambda t,m:QMessageBox.critical(self,t,m))
    def _toggle_advanced(self):self.advanced.setVisible(not self.advanced.isVisible())
    def pick_files(self):files,_=QFileDialog.getOpenFileNames(self,"Add audio tracks","","Audio files (*.*)");self.add_files(files)
    def add_files(self,files):
        existing={self.queue.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.queue.count())}
        for file in files:
            if file not in existing:self.queue.addItem(Path(file).name);self.queue.item(self.queue.count()-1).setData(Qt.ItemDataRole.UserRole,file);existing.add(file)
        self._refresh_enabled()
    def _refresh_enabled(self):self.separate.setEnabled(self.controller is not None and not self.controller.busy and self.queue.count()>0)
    def start(self):
        if not self.controller:return
        files=[self.queue.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.queue.count())]; opts={"segment":self.segment.value(),"overlap":self.overlap.value(),"shifts":self.shifts.value(),"gain":self.gain.value(),"subtype":self.depth.currentData()}; self.progress.setValue(0); self.controller.load_model_and_start(self.model.currentData(),files,opts)
    def _progress(self,r,v):self.progress.setValue(int(v*100));self._set_row(r,f"⏳ {Path(self.queue.item(r).data(Qt.ItemDataRole.UserRole)).name} • {int(v*100)}%")
    def _finished(self,r,s):self._set_row(r,("✓ " if s==5 else "✕ ")+Path(self.queue.item(r).data(Qt.ItemDataRole.UserRole)).name)
    def _set_row(self,r,t):
        if 0<=r<self.queue.count():self.queue.item(r).setText(t)
