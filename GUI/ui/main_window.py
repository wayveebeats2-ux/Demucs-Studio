from pathlib import Path
from PySide6.QtCore import Qt,Signal,QSize
from PySide6.QtGui import QIcon,QPixmap
from PySide6.QtWidgets import (QComboBox,QDoubleSpinBox,QFileDialog,QFrame,QHBoxLayout,QLabel,QListWidget,QMainWindow,QMessageBox,QProgressBar,QPushButton,QSpinBox,QVBoxLayout,QWidget,QStackedWidget,QCheckBox,QScrollArea)
from ui.drop_zone import DropZone
from ui.stem_results import StemResults
from ui.media_info import MediaInfoLoader
from ui.library_view import LibraryView
from ui.theme import DARK_STYLESHEET

class StudioWindow(QMainWindow):
    deviceChanged=Signal(str); statusChanged=Signal(str); backendReady=Signal(); busyChanged=Signal(bool); modelProgress=Signal(float); trackProgress=Signal(int,float); trackStarted=Signal(int,str); trackStatus=Signal(int,int); trackFinished=Signal(int,int); allFinished=Signal(); errorRaised=Signal(str,str); resultsReady=Signal(int,str,list); libraryChanged=Signal(); drumSubstemsReady=Signal(int,object)
    def __init__(self):
        super().__init__(); self.controller=None; self.setWindowTitle("Demucs Studio"); root_dir=Path(__file__).resolve().parents[2]; icon_path=root_dir/"assets"/"branding"/"demucs_studio_icon.png"; self.setWindowIcon(QIcon(str(icon_path))); self.resize(1120,780); self.setMinimumSize(840,620); self.setStyleSheet(DARK_STYLESHEET); self.media=MediaInfoLoader(self); self._build(); self._connect_signals(); self.media.ready.connect(self._metadata_ready)
    def attach_controller(self,c):
        self.controller=c; self.results.drumRefineRequested.connect(c.refine_drums)
    def _build(self):
        root=QWidget(); o=QVBoxLayout(root); o.setContentsMargins(22,22,22,22); o.setSpacing(14)
        header=QFrame(); header.setObjectName("header"); h=QHBoxLayout(header); brandbox=QVBoxLayout(); brand=QLabel(); brand_path=Path(__file__).resolve().parents[2]/"assets"/"branding"/"demucs_studio_wordmark@2x.png"; brand_px=QPixmap(str(brand_path)); brand.setPixmap(brand_px.scaledToHeight(34,Qt.TransformationMode.SmoothTransformation) if not brand_px.isNull() else QPixmap()); brand.setFixedHeight(38); brand.setToolTip("Demucs Studio"); subtitle=QLabel("AI POWERED STEM SEPARATION  •  FORK OF DEMUCS GUI BY CARL GAO"); subtitle.setObjectName("subtitle"); brandbox.addWidget(brand); brandbox.addWidget(subtitle); self.device=QLabel("●  Starting backend…"); self.device.setObjectName("accent"); h.addLayout(brandbox); h.addStretch(); deviceCard=QFrame(); deviceCard.setObjectName("deviceCard"); dh=QHBoxLayout(deviceCard); dh.setContentsMargins(14,8,14,8); dh.addWidget(self.device); h.addWidget(deviceCard); workspace=QPushButton("SEPARATE"); library=QPushButton("LIBRARY"); settings_btn=QPushButton("SETTINGS"); h.addWidget(workspace); h.addWidget(library); h.addWidget(settings_btn); o.addWidget(header)
        self.workspace=QWidget(); work=QVBoxLayout(self.workspace); work.setContentsMargins(0,0,0,0); work.setSpacing(14); self.drop=DropZone(); self.drop.filesDropped.connect(self.add_files); self.drop.clicked.connect(self.pick_files); work.addWidget(self.drop)
        controls=QFrame(); controls.setObjectName("panel"); cv=QVBoxLayout(controls); cv.setContentsMargins(10,8,10,10); cv.setSpacing(6); selectorRow=QHBoxLayout(); selectorRow.setSpacing(8); cv.addLayout(selectorRow); presetCol=QVBoxLayout(); presetCol.setSpacing(5); modelCol=QVBoxLayout(); modelCol.setSpacing(5); pLabel=QLabel("1. CHOOSE PRESET"); pLabel.setObjectName("section"); mLabel=QLabel("2. SELECT MODEL"); mLabel.setObjectName("section"); presetCol.addWidget(pLabel); modelCol.addWidget(mLabel); self.preset=QComboBox(); self.preset.addItem("4 Stem • Vocals / Drums / Bass / Other","four"); self.preset.addItem("Vocals + Instrumental • 2 Stem","vocals"); self.preset.addItem("6 Stem","six"); self.preset.currentIndexChanged.connect(self._preset_changed); self.model=QComboBox(); self.model.addItem("htdemucs • Recommended","htdemucs"); self.model.addItem("htdemucs_ft • Higher quality","htdemucs_ft"); self.model.addItem("htdemucs_6s • 6 stem","htdemucs_6s"); self.model.addItem("hdemucs_mmi • Hybrid Demucs MMI","hdemucs_mmi"); self.model.addItem("mdx • MDX","mdx"); self.model.addItem("mdx_extra • MDX Extra","mdx_extra"); self.model.addItem("mdx_q • MDX Quantized","mdx_q"); self.model.addItem("mdx_extra_q • MDX Extra Quantized","mdx_extra_q"); presetCol.addWidget(self.preset); modelCol.addWidget(self.model); selectorRow.addLayout(presetCol,2); selectorRow.addLayout(modelCol,2); c=QHBoxLayout(); c.setSpacing(8); cv.addLayout(c); add=QPushButton("Add Tracks"); add.clicked.connect(self.pick_files); addfolder=QPushButton("Add Folder"); addfolder.clicked.connect(self.pick_folder); remove=QPushButton("Remove"); remove.clicked.connect(self.remove_selected); clear=QPushButton("Clear All"); clear.setObjectName("danger"); clear.clicked.connect(self.clear_queue); adv=QPushButton("Advanced"); adv.clicked.connect(self._toggle_advanced); self.separate=QPushButton("SEPARATE"); self.separate.setObjectName("primary"); self.separate.setEnabled(False); self.separate.clicked.connect(self.start); c.addStretch(4); c.addWidget(add); c.addWidget(addfolder); c.addWidget(remove); c.addWidget(clear); c.addWidget(adv); c.addWidget(self.separate); work.addWidget(controls)
        self.advanced=QFrame(); self.advanced.setObjectName("panel"); a=QHBoxLayout(self.advanced); self.segment=QDoubleSpinBox(); self.segment.setRange(.1,3600); self.segment.setValue(7.8); self.segment.setSuffix(" s"); self.overlap=QDoubleSpinBox(); self.overlap.setRange(0,.99); self.overlap.setSingleStep(.05); self.overlap.setValue(.25); self.shifts=QSpinBox(); self.shifts.setRange(1,20); self.shifts.setValue(1); self.gain=QDoubleSpinBox(); self.gain.setRange(-24,24); self.gain.setSuffix(" dB"); self.depth=QComboBox(); self.depth.addItem("24-bit WAV","PCM_24"); self.depth.addItem("16-bit WAV","PCM_16"); self.depth.addItem("32-bit float WAV","FLOAT"); self.output_dir=""; self.collision=QComboBox(); self.collision.addItem("Rename existing","rename"); self.collision.addItem("Overwrite existing","overwrite"); self.collision.addItem("Skip existing","skip"); outbtn=QPushButton("Output Folder"); outbtn.clicked.connect(self.pick_output);
        for label,w in [("Segment",self.segment),("Overlap",self.overlap),("Shifts",self.shifts),("Input gain",self.gain),("Output",self.depth),("Existing",self.collision)]:a.addWidget(QLabel(label));a.addWidget(w)
        a.addWidget(outbtn)
        self.advanced.hide(); work.addWidget(self.advanced)
        self._restore_settings()
        body=QHBoxLayout(); queue_panel=QFrame(); queue_panel.setObjectName("panel"); q=QVBoxLayout(queue_panel); title=QLabel("TRACK QUEUE"); title.setObjectName("section"); q.addWidget(title); self.queue=QListWidget(); q.addWidget(self.queue,1); self.progress=QProgressBar(); self.progress.setRange(0,100); q.addWidget(self.progress); body.addWidget(queue_panel,3); self.results=StemResults(); self.results.setSizePolicy(self.results.sizePolicy().horizontalPolicy(),self.results.sizePolicy().Policy.Maximum); results_scroll=QScrollArea(); results_scroll.setWidgetResizable(True); results_scroll.setFrameShape(QFrame.Shape.NoFrame); results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); results_scroll.setWidget(self.results); results_scroll.setObjectName("resultsScroll"); body.addWidget(results_scroll,2); work.addLayout(body,1); self.library=LibraryView(); self.library.openSession.connect(self._open_library)
        self.settings_page=QWidget(); sv=QVBoxLayout(self.settings_page); sv.setContentsMargins(0,0,0,0); sv.setSpacing(14)
        settings_panel=QFrame(); settings_panel.setObjectName("panel"); sp=QVBoxLayout(settings_panel); st=QLabel("⚙  SETTINGS"); st.setObjectName("section"); sp.addWidget(st)
        info=QLabel("Studio defaults are saved automatically and used for future separations."); info.setObjectName("muted"); sp.addWidget(info)
        defaults=QFrame(); defaults.setObjectName("deviceCard"); dv=QVBoxLayout(defaults); dt=QLabel("PROCESSING DEFAULTS"); dt.setObjectName("section"); dv.addWidget(dt)
        self.settings_preset=QComboBox(); self.settings_preset.addItem("4 Stem • Vocals / Drums / Bass / Other","four"); self.settings_preset.addItem("Vocals + Instrumental • 2 Stem","vocals"); self.settings_preset.addItem("6 Stem","six")
        self.settings_model=QComboBox()
        for i in range(self.model.count()): self.settings_model.addItem(self.model.itemText(i),self.model.itemData(i))
        self.settings_segment=QDoubleSpinBox(); self.settings_segment.setRange(.1,3600); self.settings_segment.setSuffix(" s")
        self.settings_overlap=QDoubleSpinBox(); self.settings_overlap.setRange(0,.99); self.settings_overlap.setSingleStep(.05)
        self.settings_shifts=QSpinBox(); self.settings_shifts.setRange(1,20)
        self.settings_gain=QDoubleSpinBox(); self.settings_gain.setRange(-24,24); self.settings_gain.setSuffix(" dB")
        self.settings_depth=QComboBox(); self.settings_depth.addItem("24-bit WAV","PCM_24"); self.settings_depth.addItem("16-bit WAV","PCM_16"); self.settings_depth.addItem("32-bit float WAV","FLOAT")
        self.settings_collision=QComboBox(); self.settings_collision.addItem("Rename existing","rename"); self.settings_collision.addItem("Overwrite existing","overwrite"); self.settings_collision.addItem("Skip existing","skip")
        self.settings_safe_gpu=QCheckBox("8 GB GPU safe mode"); self.settings_safe_gpu.setToolTip("Uses conservative segment sizes for memory-heavy secondary models."); import shared; self.settings_safe_gpu.setChecked(bool((shared.GetHistory("studio_prefs",default={}) or {}).get("safe_gpu",True)))
        for label,widget in [("Preset",self.settings_preset),("Model",self.settings_model),("Segment length",self.settings_segment),("Overlap",self.settings_overlap),("Shifts",self.settings_shifts),("Input gain",self.settings_gain),("Output format",self.settings_depth),("Existing files",self.settings_collision)]:
            rr=QHBoxLayout(); rr.addWidget(QLabel(label)); rr.addStretch(); rr.addWidget(widget); dv.addLayout(rr)
        gpu_row=QHBoxLayout(); gpu_row.addWidget(QLabel("GPU memory")); gpu_row.addStretch(); gpu_row.addWidget(self.settings_safe_gpu); dv.addLayout(gpu_row)
        self._sync_settings_from_workspace()
        output_row=QHBoxLayout(); output_row.addWidget(QLabel("Default output folder")); self.settings_output_value=QLabel(self.output_dir or "Source-relative / separated"); self.settings_output_value.setObjectName("muted"); output_row.addWidget(self.settings_output_value,1); choose_output=QPushButton("Choose…")
        def choose_settings_output():
            folder=QFileDialog.getExistingDirectory(self,"Choose output folder",self.output_dir or str(Path.home()))
            if folder:self.output_dir=folder; self.settings_output_value.setText(folder)
        choose_output.clicked.connect(choose_settings_output); output_row.addWidget(choose_output); dv.addLayout(output_row); sp.addWidget(defaults)
        playback=QFrame(); playback.setObjectName("deviceCard"); pv=QVBoxLayout(playback); pt=QLabel("PLAYBACK & LIBRARY"); pt.setObjectName("section"); pv.addWidget(pt)
        self.settings_stop_other=QCheckBox("Pause the other mixer when audition starts"); self.settings_stop_other.setChecked(True); self.settings_auto_library=QCheckBox("Automatically add completed separations to Library"); self.settings_auto_library.setChecked(True); pv.addWidget(self.settings_stop_other); pv.addWidget(self.settings_auto_library); sp.addWidget(playback)
        advanced_settings=QFrame(); advanced_settings.setObjectName("deviceCard"); av=QVBoxLayout(advanced_settings); at=QLabel("ADVANCED"); at.setObjectName("section"); av.addWidget(at); diagnostics=QLabel("Models are cached by Demucs on first use. FFmpeg and backend diagnostics are reported in the status bar."); diagnostics.setWordWrap(True); diagnostics.setObjectName("muted"); av.addWidget(diagnostics); sp.addWidget(advanced_settings)
        actions=QHBoxLayout(); save_settings=QPushButton("Save Settings"); save_settings.setObjectName("primary"); save_settings.clicked.connect(self._apply_settings_page); reset_settings=QPushButton("Reset Defaults"); reset_settings.clicked.connect(self._reset_settings); actions.addWidget(save_settings); actions.addWidget(reset_settings); actions.addStretch(); sp.addLayout(actions); sp.addStretch(); sv.addWidget(settings_panel,1)
        self.stack=QStackedWidget(); self.stack.addWidget(self.workspace); self.stack.addWidget(self.library); self.stack.addWidget(self.settings_page); o.addWidget(self.stack,1); workspace.clicked.connect(lambda:self.stack.setCurrentWidget(self.workspace)); library.clicked.connect(lambda:self.stack.setCurrentWidget(self.library)); settings_btn.clicked.connect(lambda:self.stack.setCurrentWidget(self.settings_page)); self.status=QLabel("●  Initializing Demucs…"); self.status.setObjectName("muted"); o.addWidget(self.status); self.setCentralWidget(root)
    def _connect_signals(self):
        self.deviceChanged.connect(self.device.setText); self.statusChanged.connect(self.status.setText); self.backendReady.connect(self._refresh_enabled); self.busyChanged.connect(lambda b:self.separate.setEnabled(not b and self.queue.count()>0)); self.trackProgress.connect(self._progress); self.trackStarted.connect(lambda r,n:self._set_row(r,f"⏳ {n}")); self.trackFinished.connect(self._finished); self.resultsReady.connect(self.results.show_results); self.allFinished.connect(lambda:self.progress.setValue(100)); self.errorRaised.connect(lambda t,m:QMessageBox.critical(self,t,m)); self.libraryChanged.connect(self.library.reload); self.drumSubstemsReady.connect(self.results.add_drum_substems)
    def _open_library(self,entry):
        outputs=[(a,b) for a,b in entry.get("outputs",[]) if Path(b).exists()]
        if not outputs:
            QMessageBox.warning(self,"Missing stems","The indexed stem files could not be found."); return
        self.results.show_results(-abs(hash(entry.get("folder","")))%1000000,entry.get("folder",""),outputs)
        self.stack.setCurrentWidget(self.workspace)
    def _toggle_advanced(self):self.advanced.setVisible(not self.advanced.isVisible())
    def pick_files(self):files,_=QFileDialog.getOpenFileNames(self,"Add audio tracks","","Audio files (*.*)");self.add_files(files)
    def pick_folder(self):
        folder=QFileDialog.getExistingDirectory(self,"Add audio folder")
        if folder:
            exts={".wav",".flac",".mp3",".m4a",".aac",".ogg",".opus",".wma",".aiff",".aif"}
            self.add_files([str(p) for p in Path(folder).rglob("*") if p.is_file() and p.suffix.lower() in exts])
    def pick_output(self):
        folder=QFileDialog.getExistingDirectory(self,"Choose output folder",self.output_dir or str(Path.home()))
        if folder:self.output_dir=folder;self.status.setText("Output: "+folder)
    def add_files(self,files):
        exts={".wav",".flac",".mp3",".m4a",".aac",".ogg",".opus",".wma",".aiff",".aif"}
        expanded=[]
        for raw in files:
            p=Path(raw)
            if p.is_dir(): expanded.extend(str(x) for x in p.rglob("*") if x.is_file() and x.suffix.lower() in exts)
            elif p.is_file() and p.suffix.lower() in exts: expanded.append(str(p))
        existing={self.queue.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.queue.count())}
        added=0
        for file in expanded:
            if file not in existing:
                self.queue.addItem("◌  "+Path(file).name+"\\n    Reading metadata…"); item=self.queue.item(self.queue.count()-1); item.setData(Qt.ItemDataRole.UserRole,file); item.setSizeHint(QSize(0,58)); existing.add(file); self.media.request(file); added+=1
        if files and not added and not any(str(x) in existing for x in expanded):
            QMessageBox.warning(self,"No audio added","No supported audio files were found.")
        self._refresh_enabled()
    @staticmethod
    def _duration(seconds):
        seconds=int(seconds or 0); return f"{seconds//60}:{seconds%60:02d}" if seconds else "--:--"
    @staticmethod
    def _size(n):
        return f"{n/1048576:.1f} MB" if n else "—"
    def _metadata_ready(self,path,info):
        for i in range(self.queue.count()):
            item=self.queue.item(i)
            if item.data(Qt.ItemDataRole.UserRole)==path:
                title=info.get("title") or Path(path).stem; artist=info.get("artist") or "Unknown artist"
                item.setText(f"♫  {title}\\n    {artist}   •   {self._duration(info.get('duration'))}   •   {self._size(info.get('size'))}")
                art=info.get("artwork")
                if art:
                    px=QPixmap(); px.loadFromData(art); item.setIcon(QIcon(px))
                    self.queue.setIconSize(QSize(42,42))
                item.setData(Qt.ItemDataRole.UserRole+1,info); break
    def _refresh_enabled(self):self.separate.setEnabled(self.controller is not None and not self.controller.busy and self.queue.count()>0)
    def start(self):
        if not self.controller:return
        files=[self.queue.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.queue.count())]; self._save_settings(); opts={"preset":self.preset.currentData(),"segment":self.segment.value(),"overlap":self.overlap.value(),"shifts":self.shifts.value(),"gain":self.gain.value(),"subtype":self.depth.currentData(),"output_dir":self.output_dir,"collision":self.collision.currentData(),"safe_gpu":getattr(self,"settings_safe_gpu",None).isChecked() if hasattr(self,"settings_safe_gpu") else True}; self.progress.setValue(0); self.controller.load_model_and_start(self.model.currentData(),files,opts)
    def _preset_changed(self):
        if self.preset.currentData()=="six": self.model.setCurrentIndex(self.model.findData("htdemucs_6s"))
        elif self.model.currentData()=="htdemucs_6s": self.model.setCurrentIndex(self.model.findData("htdemucs"))
    def remove_selected(self):
        if self.controller and self.controller.busy:return
        for item in self.queue.selectedItems(): self.queue.takeItem(self.queue.row(item))
        self._refresh_enabled()
    def clear_queue(self):
        if self.controller and self.controller.busy:return
        self.queue.clear(); self.progress.setValue(0); self._refresh_enabled()
    def _sync_settings_from_workspace(self):
        pairs=[(self.settings_preset,self.preset),(self.settings_model,self.model),(self.settings_depth,self.depth),(self.settings_collision,self.collision)]
        for target,source in pairs:
            idx=target.findData(source.currentData())
            if idx>=0: target.setCurrentIndex(idx)
        self.settings_segment.setValue(self.segment.value()); self.settings_overlap.setValue(self.overlap.value()); self.settings_shifts.setValue(self.shifts.value()); self.settings_gain.setValue(self.gain.value())

    def _apply_settings_page(self):
        pairs=[(self.preset,self.settings_preset),(self.model,self.settings_model),(self.depth,self.settings_depth),(self.collision,self.settings_collision)]
        for target,source in pairs:
            idx=target.findData(source.currentData())
            if idx>=0: target.setCurrentIndex(idx)
        self.segment.setValue(self.settings_segment.value()); self.overlap.setValue(self.settings_overlap.value()); self.shifts.setValue(self.settings_shifts.value()); self.gain.setValue(self.settings_gain.value()); self._save_settings(); self.status.setText("Settings saved")

    def _reset_settings(self):
        self.preset.setCurrentIndex(self.preset.findData("four")); self.model.setCurrentIndex(self.model.findData("htdemucs")); self.segment.setValue(7.8); self.overlap.setValue(.25); self.shifts.setValue(1); self.gain.setValue(0); self.depth.setCurrentIndex(self.depth.findData("PCM_24")); self.collision.setCurrentIndex(self.collision.findData("rename")); self.output_dir=""
        if hasattr(self,"settings_safe_gpu"): self.settings_safe_gpu.setChecked(True); self._sync_settings_from_workspace(); self.settings_output_value.setText("Source-relative / separated")
        self._save_settings(); self.status.setText("Settings reset to defaults")

    def _save_settings(self):
        import shared
        shared.SetHistory("studio_prefs",value={"preset":self.preset.currentData(),"model":self.model.currentData(),"segment":self.segment.value(),"overlap":self.overlap.value(),"shifts":self.shifts.value(),"gain":self.gain.value(),"subtype":self.depth.currentData(),"output_dir":self.output_dir,"collision":self.collision.currentData(),"safe_gpu":self.settings_safe_gpu.isChecked() if hasattr(self,"settings_safe_gpu") else True})
    def _restore_settings(self):
        import shared
        p=shared.GetHistory("studio_prefs",default={}) or {}; self.output_dir=p.get("output_dir","")
        if self.preset.findData(p.get("preset"))>=0:self.preset.setCurrentIndex(self.preset.findData(p["preset"]))
        if self.model.findData(p.get("model"))>=0:self.model.setCurrentIndex(self.model.findData(p["model"]))
        self.segment.setValue(float(p.get("segment",7.8))); self.overlap.setValue(float(p.get("overlap",.25))); self.shifts.setValue(int(p.get("shifts",1))); self.gain.setValue(float(p.get("gain",0)))
        if self.depth.findData(p.get("subtype"))>=0:self.depth.setCurrentIndex(self.depth.findData(p["subtype"]))
        if self.collision.findData(p.get("collision"))>=0:self.collision.setCurrentIndex(self.collision.findData(p["collision"]))
    def _progress(self,r,v):self.progress.setValue(int(v*100));self._set_row(r,f"⏳ {Path(self.queue.item(r).data(Qt.ItemDataRole.UserRole)).name} • {int(v*100)}%")
    def _finished(self,r,s):self._set_row(r,("✓ " if s==5 else "✕ ")+Path(self.queue.item(r).data(Qt.ItemDataRole.UserRole)).name)
    def _set_row(self,r,t):
        if 0<=r<self.queue.count():self.queue.item(r).setText(t)
