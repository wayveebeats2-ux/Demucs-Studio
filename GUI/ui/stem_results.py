import os,sys,subprocess
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox,QFileDialog,QFrame,QHBoxLayout,QLabel,QPushButton,QSlider,QVBoxLayout
from ui.waveform import WaveformLoader,WaveformWidget
from ui.audition import AuditionMixer

class StemResults(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent); self.setObjectName("panel"); self.groups={}; self.waveforms={}; self.loader=WaveformLoader(self); self.loader.ready.connect(self._wave_ready); self.mixer=AuditionMixer(self); self.active_row=None; self.transport_slider=None; self.time_label=None; self.play_button=None
        self.layout=QVBoxLayout(self); title=QLabel("♫  RESULTS"); title.setObjectName("section"); self.layout.addWidget(title); self.hint=QLabel("Completed stems will appear here."); self.hint.setObjectName("muted"); self.layout.addWidget(self.hint)
    def show_results(self,row,folder,outputs):
        self.hint.hide(); divider=QFrame(); divider.setFrameShape(QFrame.Shape.HLine); self.layout.addWidget(divider); group={"folder":folder,"stems":list(outputs),"state":{stem:{"mute":False,"solo":False,"db":0.0} for stem,_ in outputs}}; self.groups[row]=group
        head=QHBoxLayout(); label=QLabel("✓  "+Path(folder).parent.name); label.setObjectName("success"); audition=QPushButton("▶ Play Mix"); audition.setObjectName("primary"); stop=QPushButton("■ Stop"); export=QPushButton("Export Mix"); export.clicked.connect(lambda checked=False,r=row:self._export_mix(r)); open_btn=QPushButton("Open Folder"); audition.clicked.connect(lambda checked=False,r=row:self._toggle_mix(r)); stop.clicked.connect(self.mixer.stop); open_btn.clicked.connect(lambda:self.open_folder(folder)); head.addWidget(label); head.addStretch(); head.addWidget(audition); head.addWidget(stop); head.addWidget(export); head.addWidget(open_btn); self.layout.addLayout(head)
        transport=QHBoxLayout(); timeline=QSlider(Qt.Orientation.Horizontal); timeline.setRange(0,0); timeline.setTracking(True); clock=QLabel("0:00 / 0:00"); clock.setObjectName("muted"); timeline.sliderMoved.connect(lambda ms,r=row:self._seek(r,ms)); transport.addWidget(timeline,1); transport.addWidget(clock); self.layout.addLayout(transport)
        group["timeline"]=timeline; group["clock"]=clock; group["play_button"]=audition
        self.mixer.positionChanged.connect(lambda ms,r=row:self._position(r,ms)); self.mixer.durationChanged.connect(lambda ms,r=row:self._duration(r,ms)); self.mixer.playingChanged.connect(lambda playing,r=row:self._playing(r,playing))
        for stem,file in outputs:
            line=QHBoxLayout(); name=QLabel("●  "+stem.title()); name.setObjectName("accent"); name.setMinimumWidth(90); solo=QCheckBox("S"); solo.setToolTip("Solo"); mute=QCheckBox("M"); mute.setToolTip("Mute"); volume=QSlider(Qt.Orientation.Horizontal); volume.setRange(-24,6); volume.setValue(0); volume.setFixedWidth(75); volume.setToolTip("Stem audition gain (dB)"); wave=WaveformWidget(); self.waveforms[file]=wave; group.setdefault("waves",[]).append(wave); wave.seekRequested.connect(lambda fraction,r=row:self._wave_seek(r,fraction))
            solo.toggled.connect(lambda v,r=row,s=stem:self._state(r,s,"solo",v)); mute.toggled.connect(lambda v,r=row,s=stem:self._state(r,s,"mute",v)); volume.valueChanged.connect(lambda v,r=row,s=stem:self._state(r,s,"db",float(v)))
            line.addWidget(name); line.addWidget(solo); line.addWidget(mute); line.addWidget(volume); line.addWidget(wave,1); self.layout.addLayout(line); self.loader.request(file)
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
        self.active_row=row; g=self.groups[row]; self.mixer.load(row,g["stems"],g["state"]); self.mixer.play()
    def _export_mix(self,row):
        g=self.groups[row]; default=str(Path(g["folder"])/"audition_mix.wav"); target,_=QFileDialog.getSaveFileName(self,"Export audition mix",default,"WAV audio (*.wav)")
        if target:self.mixer.export(row,g["stems"],g["state"],target)
    @staticmethod
    def _fmt(ms):
        sec=max(0,int(ms)//1000); return f"{sec//60}:{sec%60:02d}"
    def _position(self,row,ms):
        if row!=self.active_row:return
        g=self.groups.get(row)
        if g and not g["timeline"].isSliderDown():g["timeline"].setValue(ms)
        if g and g["timeline"].maximum()>0:
            progress=float(ms)/g["timeline"].maximum()
            for wave in g.get("waves",[]):wave.set_progress(progress)
        if g:g["clock"].setText(f"{self._fmt(ms)} / {self._fmt(g['timeline'].maximum())}")
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
