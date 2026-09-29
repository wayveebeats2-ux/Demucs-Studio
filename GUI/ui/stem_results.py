import os,sys,subprocess
from pathlib import Path
from PySide6.QtCore import Qt,Signal
from PySide6.QtWidgets import QCheckBox,QDialog,QFileDialog,QFrame,QHBoxLayout,QLabel,QPushButton,QSlider,QVBoxLayout,QStyle,QWidget
from ui.waveform import WaveformLoader,WaveformWidget
from ui.audition import AuditionMixer

class SeekSlider(QSlider):
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            value=QStyle.sliderValueFromPosition(self.minimum(),self.maximum(),int(event.position().x()),max(1,self.width()))
            self.setValue(value); self.sliderMoved.emit(value); event.accept(); return
        super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            value=QStyle.sliderValueFromPosition(self.minimum(),self.maximum(),int(event.position().x()),max(1,self.width()))
            self.setValue(value); self.sliderMoved.emit(value); event.accept(); return
        super().mouseMoveEvent(event)

class StemResults(QFrame):
    drumRefineRequested=Signal(int,str,str)
    def __init__(self,parent=None):
        super().__init__(parent); self.setObjectName("panel"); self.groups={}; self.waveforms={}; self.loader=WaveformLoader(self); self.loader.ready.connect(self._wave_ready); self.mixer=AuditionMixer(self); self.drum_mixer=AuditionMixer(self); self.active_row=None; self.active_drum_row=None; self.transport_slider=None; self.time_label=None; self.play_button=None; self.expanded=[]
        self.mixer.positionChanged.connect(self._active_position); self.mixer.durationChanged.connect(self._active_duration); self.mixer.playingChanged.connect(self._active_playing)
        self.layout=QVBoxLayout(self); title=QLabel("♫  RESULTS"); title.setObjectName("section"); self.layout.addWidget(title); self.hint=QLabel("Completed stems will appear here."); self.hint.setObjectName("muted"); self.layout.addWidget(self.hint)
    def show_results(self,row,folder,outputs):
        self.hint.hide(); divider=QFrame(); divider.setFrameShape(QFrame.Shape.HLine); self.layout.addWidget(divider); group={"folder":folder,"stems":list(outputs),"state":{stem:{"mute":False,"solo":False,"db":0.0} for stem,_ in outputs}}; self.groups[row]=group
        head=QHBoxLayout(); label=QLabel("✓  "+Path(folder).name); label.setObjectName("success"); audition=QPushButton("▶ Play Mix"); audition.setObjectName("primary"); stop=QPushButton("■ Stop"); export=QPushButton("Export Mix"); export.clicked.connect(lambda checked=False,r=row:self._export_mix(r)); open_btn=QPushButton("Open Folder"); audition.clicked.connect(lambda checked=False,r=row:self._toggle_mix(r)); stop.clicked.connect(self.mixer.stop); open_btn.clicked.connect(lambda:self.open_folder(folder)); head.addWidget(label); head.addStretch(); head.addWidget(audition); head.addWidget(stop); head.addWidget(export); head.addWidget(open_btn); self.layout.addLayout(head)
        transport=QHBoxLayout(); timeline=SeekSlider(Qt.Orientation.Horizontal); timeline.setRange(0,0); timeline.setTracking(True); clock=QLabel("0:00 / 0:00"); clock.setObjectName("muted"); timeline.sliderMoved.connect(lambda ms,r=row:self._seek(r,ms)); transport.addWidget(timeline,1); transport.addWidget(clock); self.layout.addLayout(transport)
        group["timeline"]=timeline; group["clock"]=clock; group["play_button"]=audition
        for stem,file in outputs:
            line=QHBoxLayout(); name=QLabel("●  "+stem.title()); name.setObjectName("accent"); name.setMinimumWidth(90); solo=QCheckBox("S"); solo.setToolTip("Solo"); mute=QCheckBox("M"); mute.setToolTip("Mute"); volume=QSlider(Qt.Orientation.Horizontal); volume.setRange(-24,6); volume.setValue(0); volume.setFixedWidth(75); volume.setToolTip("Stem audition gain (dB)"); wave=WaveformWidget(); wave.allowDrumRefine=(stem.lower()=="drums"); self.waveforms[file]=wave; group.setdefault("waves",[]).append(wave); wave.seekRequested.connect(lambda fraction,r=row:self._wave_seek(r,fraction)); wave.expandRequested.connect(lambda r=row,s=stem,f=file:self._expand_wave(r,s,f)); wave.refineDrumsRequested.connect(lambda r=row,s=stem,f=file:self.drumRefineRequested.emit(r,f,self.groups[r]["folder"]))
            solo.toggled.connect(lambda v,r=row,s=stem:self._state(r,s,"solo",v)); mute.toggled.connect(lambda v,r=row,s=stem:self._state(r,s,"mute",v)); volume.valueChanged.connect(lambda v,r=row,s=stem:self._state(r,s,"db",float(v)))
            group.setdefault("controls",{})[stem]={"solo":solo,"mute":mute,"volume":volume}
            if stem.lower()=="drums":
                disclosure=QPushButton("▸"); disclosure.setFixedWidth(26); disclosure.hide(); disclosure.clicked.connect(lambda checked=False,r=row:self._toggle_drum_children(r)); line.insertWidget(0,disclosure); group["drum_disclosure"]=disclosure
            line.addWidget(name); line.addWidget(solo); line.addWidget(mute); line.addWidget(volume); line.addWidget(wave,1); self.layout.addLayout(line)
            if stem.lower()=="drums":
                children=QWidget(); child_layout=QVBoxLayout(children); child_layout.setContentsMargins(34,2,0,4); child_layout.setSpacing(4); children.hide(); group["drum_children_widget"]=children; group["drum_children_layout"]=child_layout; self.layout.addWidget(children)
                existing_dir=Path(folder)/"drums"; existing=[(n,str(existing_dir/f"{n}.wav")) for n in ("kick","snare","cymbals","toms") if (existing_dir/f"{n}.wav").exists()]
                if existing:self.add_drum_substems(row,existing)
            self.loader.request(file)
    def _toggle_drum_children(self,row):
        g=self.groups.get(row); w=g.get("drum_children_widget") if g else None
        if not w:return
        show=not w.isVisible(); w.setVisible(show); g["drum_disclosure"].setText("▾" if show else "▸")

    def add_drum_substems(self,row,outputs):
        g=self.groups.get(row)
        if not g or g.get("drum_children_layout") is None:return
        layout=g["drum_children_layout"]
        while layout.count():
            item=layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        g["drum_substems"]=list(outputs); g["drum_state"]={stem:{"mute":False,"solo":False,"db":0.0} for stem,_ in outputs}
        audition=QPushButton("▶ Audition Drum Stems"); audition.setObjectName("primary"); audition.clicked.connect(lambda checked=False,r=row:self._toggle_drum_mix(r)); layout.addWidget(audition); g["drum_play_button"]=audition
        for stem,file in outputs:
            key="drum:"+stem
            line=QHBoxLayout(); name=QLabel("↳  "+stem.title()); name.setObjectName("muted"); name.setMinimumWidth(90); solo=QCheckBox("S"); mute=QCheckBox("M"); gain=QSlider(Qt.Orientation.Horizontal); gain.setRange(-24,6); gain.setValue(0); gain.setFixedWidth(75); wave=WaveformWidget()
            self.waveforms[file]=wave; g.setdefault("waves",[]).append(wave); wave.seekRequested.connect(lambda fraction,r=row:self._drum_wave_seek(r,fraction)); wave.expandRequested.connect(lambda r=row,s=key,f=file:self._expand_drum_wave(r,s,f))
            solo.toggled.connect(lambda v,r=row,s=stem:self._drum_state(r,s,"solo",v)); mute.toggled.connect(lambda v,r=row,s=stem:self._drum_state(r,s,"mute",v)); gain.valueChanged.connect(lambda v,r=row,s=stem:self._drum_state(r,s,"db",float(v)))
            g.setdefault("controls",{})[key]={"solo":solo,"mute":mute,"volume":gain}; line.addWidget(name); line.addWidget(solo); line.addWidget(mute); line.addWidget(gain); line.addWidget(wave,1); layout.addLayout(line); self.loader.request(file)
        g["drum_disclosure"].show(); g["drum_children_widget"].show(); g["drum_disclosure"].setText("▾")

    def _drum_state(self,row,stem,field,value):
        g=self.groups[row]; g["drum_state"][stem][field]=value
        if row==self.active_drum_row:self.drum_mixer.apply_state()

    def _toggle_drum_mix(self,row):
        g=self.groups[row]
        if self.active_drum_row==row and self.drum_mixer.players:
            self.drum_mixer.play_pause(); return
        self.mixer.pause(); self.active_drum_row=row
        self.drum_mixer.load(int(abs(row)+10000000),g.get("drum_substems",[]),g.get("drum_state",{})); self.drum_mixer.play()

    def _drum_wave_seek(self,row,fraction):
        if row!=self.active_drum_row:return
        duration=self.drum_mixer._duration
        if duration>0:self.drum_mixer.seek(int(duration*max(0.0,min(1.0,fraction))))

    def _expand_drum_wave(self,row,stem,file):
        g=self.groups[row]; dlg=QDialog(self); dlg.setWindowTitle(f"{stem.replace('drum:','').title()} • Drum Audition"); dlg.resize(900,300)
        v=QVBoxLayout(dlg); title=QLabel(stem.replace("drum:","").upper()); title.setObjectName("section"); v.addWidget(title)
        wave=WaveformWidget(); wave.setMinimumHeight(130); src=self.waveforms.get(file)
        if src is not None:wave.set_peaks(src.peaks)
        wave.seekRequested.connect(lambda fraction,r=row:self._drum_wave_seek(r,fraction)); v.addWidget(wave,1)
        controls=QHBoxLayout(); play=QPushButton("Play / Pause Drum Stems"); stop=QPushButton("Stop"); play.clicked.connect(lambda:self._toggle_drum_mix(row)); stop.clicked.connect(self.drum_mixer.stop); controls.addWidget(play); controls.addWidget(stop); controls.addStretch(); v.addLayout(controls); dlg.show()
        entry={"dialog":dlg,"wave":wave,"clock":QLabel(),"row":None}; self.expanded.append(entry); dlg.finished.connect(lambda _=0,e=entry:self.expanded.remove(e) if e in self.expanded else None)

    def _expand_wave(self,row,stem,file):
        g=self.groups[row]; dlg=QDialog(self); dlg.setWindowTitle(f"{stem.title()} • Expanded Waveform"); dlg.resize(900,300); dlg.setMinimumSize(560,220)
        v=QVBoxLayout(dlg); top=QHBoxLayout(); title=QLabel(stem.replace("drum:","").upper()); title.setObjectName("section"); clock=QLabel(g["clock"].text()); clock.setObjectName("muted"); top.addWidget(title); top.addStretch(); top.addWidget(clock); v.addLayout(top)
        wave=WaveformWidget(); wave.setMinimumHeight(130); wave.setMaximumHeight(16777215); wave.setFixedHeight(130); wave.setSizePolicy(wave.sizePolicy().horizontalPolicy(),wave.sizePolicy().Policy.Expanding)
        src=self.waveforms.get(file)
        if src is not None: wave.set_peaks(src.peaks); wave.set_progress(src.progress)
        wave.seekRequested.connect(lambda fraction,r=row:self._wave_seek(r,fraction)); v.addWidget(wave,1)
        controls=QHBoxLayout(); solo=QCheckBox("Solo"); mute=QCheckBox("Mute"); gain=QSlider(Qt.Orientation.Horizontal); gain.setRange(-24,6); gain.setMinimumWidth(240); play=QPushButton("Play / Pause"); stop=QPushButton("Stop")
        original=g["controls"][stem]; solo.setChecked(original["solo"].isChecked()); mute.setChecked(original["mute"].isChecked()); gain.setValue(original["volume"].value())
        solo.toggled.connect(original["solo"].setChecked); mute.toggled.connect(original["mute"].setChecked); gain.valueChanged.connect(original["volume"].setValue); play.clicked.connect(lambda:self._toggle_mix(row)); stop.clicked.connect(self.mixer.stop)
        controls.addWidget(solo); controls.addWidget(mute); controls.addWidget(QLabel("Gain")); controls.addWidget(gain,1); controls.addWidget(play); controls.addWidget(stop); v.addLayout(controls)
        entry={"dialog":dlg,"wave":wave,"clock":clock,"row":row}; self.expanded.append(entry); dlg.finished.connect(lambda _=0,e=entry:self.expanded.remove(e) if e in self.expanded else None); dlg.show()
    def _state(self,row,stem,key,value):
        self.groups[row]["state"][stem][key]=value
        if row==self.active_row:self.mixer.apply_state()
    def _seek(self,row,ms):
        if row==self.active_row:self.mixer.seek(ms)
    def _wave_seek(self,row,fraction):
        if row!=self.active_row:return
        g=self.groups[row]; duration=g["timeline"].maximum()
        if duration>0:
            fraction=max(0.0,min(1.0,fraction)); target=int(duration*fraction)
            g["timeline"].setValue(target); g["clock"].setText(f"{self._fmt(target)} / {self._fmt(duration)}")
            for wave in g.get("waves",[]):wave.set_progress(fraction)
            self.mixer.seek(target)
    def _toggle_mix(self,row):
        if self.active_row==row and self.mixer.players:
            self.mixer.play_pause(); return
        self.drum_mixer.pause(); self.active_row=row; g=self.groups[row]; self.mixer.load(row,g["stems"],g["state"]); self.mixer.play()
    def _export_mix(self,row):
        g=self.groups[row]; default=str(Path(g["folder"])/"audition_mix.wav"); target,_=QFileDialog.getSaveFileName(self,"Export audition mix",default,"WAV audio (*.wav)")
        if target:self.mixer.export(row,g["stems"],g["state"],target)
    @staticmethod
    def _fmt(ms):
        sec=max(0,int(ms)//1000); return f"{sec//60}:{sec%60:02d}"
    def _active_position(self,ms):
        if self.active_row is not None:self._position(self.active_row,ms)
    def _active_duration(self,ms):
        if self.active_row is not None:self._duration(self.active_row,ms)
    def _active_playing(self,playing):
        if self.active_row is not None:self._playing(self.active_row,playing)
    def _position(self,row,ms):
        if row!=self.active_row:return
        g=self.groups.get(row)
        if g and not g["timeline"].isSliderDown():g["timeline"].setValue(ms)
        if g and g["timeline"].maximum()>0:
            progress=float(ms)/g["timeline"].maximum()
            for wave in g.get("waves",[]):wave.set_progress(progress)
        if g:g["clock"].setText(f"{self._fmt(ms)} / {self._fmt(g['timeline'].maximum())}")
        for e in self.expanded:
            if e["row"]==row:
                e["wave"].set_progress(float(ms)/g["timeline"].maximum() if g and g["timeline"].maximum()>0 else 0); e["clock"].setText(g["clock"].text())
    def _duration(self,row,ms):
        if row!=self.active_row:return
        g=self.groups.get(row)
        if g:g["timeline"].setRange(0,ms);g["clock"].setText(f"0:00 / {self._fmt(ms)}")
    def _playing(self,row,playing):
        if row!=self.active_row:return
        g=self.groups.get(row)
        if g:g["play_button"].setText("Ⅱ Pause" if playing else "▶ Play Mix")
    def _wave_ready(self,path,peaks):
        if path in self.waveforms:self.waveforms[path].set_peaks(peaks)
    @staticmethod
    def show_file(file):
        if sys.platform=="win32":subprocess.Popen(["explorer","/select,",str(Path(file))])
        else:StemResults.open_folder(str(Path(file).parent))
    @staticmethod
    def open_folder(folder):
        if sys.platform=="win32":os.startfile(folder)
        elif sys.platform=="darwin":subprocess.Popen(["open",folder])
        else:subprocess.Popen(["xdg-open",folder])
