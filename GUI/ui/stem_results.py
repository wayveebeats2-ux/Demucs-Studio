import os,sys,subprocess
from pathlib import Path
from PySide6.QtCore import QUrl,Qt
from PySide6.QtMultimedia import QAudioOutput,QMediaPlayer
from PySide6.QtWidgets import QCheckBox,QFileDialog,QFrame,QHBoxLayout,QLabel,QPushButton,QSlider,QVBoxLayout
from ui.waveform import WaveformLoader,WaveformWidget
from ui.audition import AuditionMixer

class StemResults(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent); self.setObjectName("panel"); self.players=[]; self.groups={}; self.waveforms={}; self.loader=WaveformLoader(self); self.loader.ready.connect(self._wave_ready); self.mixer=AuditionMixer(self)
        self.layout=QVBoxLayout(self); title=QLabel("♫  RESULTS"); title.setObjectName("section"); self.layout.addWidget(title); self.hint=QLabel("Completed stems will appear here."); self.hint.setObjectName("muted"); self.layout.addWidget(self.hint)
    def show_results(self,row,folder,outputs):
        self.hint.hide(); divider=QFrame(); divider.setFrameShape(QFrame.Shape.HLine); self.layout.addWidget(divider); group={"folder":folder,"stems":list(outputs),"state":{stem:{"mute":False,"solo":False,"db":0.0} for stem,_ in outputs}}; self.groups[row]=group
        head=QHBoxLayout(); label=QLabel("✓  "+Path(folder).parent.name); label.setObjectName("success"); audition=QPushButton("▶ Audition Mix"); audition.setObjectName("primary"); pause=QPushButton("Ⅱ"); stop=QPushButton("■"); export=QPushButton("Export Mix"); export.clicked.connect(lambda checked=False,r=row:self._export_mix(r)); open_btn=QPushButton("Open Folder"); audition.clicked.connect(lambda checked=False,r=row:self._play_mix(r)); pause.clicked.connect(self.mixer.pause); stop.clicked.connect(self.mixer.stop); open_btn.clicked.connect(lambda:self.open_folder(folder)); head.addWidget(label); head.addStretch(); head.addWidget(audition); head.addWidget(pause); head.addWidget(stop); head.addWidget(export); head.addWidget(open_btn); self.layout.addLayout(head)
        for stem,file in outputs:
            line=QHBoxLayout(); name=QLabel("●  "+stem.title()); name.setObjectName("accent"); name.setMinimumWidth(90); solo=QCheckBox("S"); solo.setToolTip("Solo"); mute=QCheckBox("M"); mute.setToolTip("Mute"); volume=QSlider(Qt.Orientation.Horizontal); volume.setRange(-24,6); volume.setValue(0); volume.setFixedWidth(75); volume.setToolTip("Stem audition gain (dB)"); wave=WaveformWidget(); self.waveforms[file]=wave
            play=QPushButton("▶"); play.setToolTip("Play this stem"); audio=QAudioOutput(self); player=QMediaPlayer(self); player.setAudioOutput(audio); player.setSource(QUrl.fromLocalFile(file)); self.players.append((player,audio)); play.clicked.connect(lambda checked=False,p=player:self._play_solo_file(p)); solo.toggled.connect(lambda v,r=row,s=stem:self._state(r,s,"solo",v)); mute.toggled.connect(lambda v,r=row,s=stem:self._state(r,s,"mute",v)); volume.valueChanged.connect(lambda v,r=row,s=stem:self._state(r,s,"db",float(v)))
            line.addWidget(name); line.addWidget(solo); line.addWidget(mute); line.addWidget(volume); line.addWidget(play); line.addWidget(wave,1); self.layout.addLayout(line); self.loader.request(file)
    def _state(self,row,stem,key,value):self.groups[row]["state"][stem][key]=value
    def _play_mix(self,row):
        for p,_ in self.players:p.stop()
        g=self.groups[row]; self.mixer.render_and_play(row,g["stems"],g["state"])
    def _export_mix(self,row):
        g=self.groups[row]; default=str(Path(g["folder"])/"audition_mix.wav"); target,_=QFileDialog.getSaveFileName(self,"Export audition mix",default,"WAV audio (*.wav)")
        if target:self.mixer.export(row,g["stems"],g["state"],target)
    def _play_solo_file(self,player):
        self.mixer.stop()
        for p,_ in self.players:
            if p is not player:p.stop()
        player.setPosition(0);player.play()
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
