import os,sys,subprocess
from pathlib import Path
from PySide6.QtCore import QUrl,QTimer
from PySide6.QtMultimedia import QAudioOutput,QMediaPlayer
from PySide6.QtWidgets import QFrame,QHBoxLayout,QLabel,QPushButton,QVBoxLayout
from ui.waveform import WaveformLoader,WaveformWidget

class StemResults(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent); self.setObjectName("panel"); self.output_dir=None; self.players=[]; self.groups={}; self.waveforms={}; self.loader=WaveformLoader(self); self.loader.ready.connect(self._wave_ready)
        self.layout=QVBoxLayout(self); title=QLabel("♫  RESULTS"); title.setObjectName("section"); self.layout.addWidget(title); self.hint=QLabel("Completed stems will appear here."); self.hint.setObjectName("muted"); self.layout.addWidget(self.hint)
    def show_results(self,row,folder,outputs):
        self.output_dir=folder; self.hint.hide(); divider=QFrame(); divider.setFrameShape(QFrame.Shape.HLine); self.layout.addWidget(divider); group=[]; self.groups[row]=group
        head=QHBoxLayout(); label=QLabel("✓  "+Path(folder).parent.name); label.setObjectName("success"); audition=QPushButton("▶ Play All"); audition.setObjectName("primary"); pause=QPushButton("Ⅱ"); pause.setToolTip("Pause all stems"); stop_all=QPushButton("■"); stop_all.setToolTip("Stop all stems"); open_btn=QPushButton("Open Folder"); open_btn.clicked.connect(lambda:self.open_folder(folder)); audition.clicked.connect(lambda checked=False,r=row:self._play_all(r)); pause.clicked.connect(lambda checked=False,r=row:self._pause_all(r)); stop_all.clicked.connect(lambda checked=False,r=row:self._stop_all(r)); head.addWidget(label); head.addStretch(); head.addWidget(audition); head.addWidget(pause); head.addWidget(stop_all); head.addWidget(open_btn); self.layout.addLayout(head)
        for stem,file in outputs:
            line=QHBoxLayout(); name=QLabel("●  "+stem.title()); name.setObjectName("accent"); name.setMinimumWidth(95); wave=WaveformWidget(); self.waveforms[file]=wave
            play=QPushButton("▶"); play.setToolTip("Solo stem"); stop=QPushButton("■"); stop.setToolTip("Stop stem"); audio=QAudioOutput(self); player=QMediaPlayer(self); player.setAudioOutput(audio); player.setSource(QUrl.fromLocalFile(file)); self.players.append((player,audio)); group.append((player,audio)); play.clicked.connect(lambda checked=False,p=player:self._play_solo(p)); stop.clicked.connect(player.stop)
            file_btn=QPushButton("Show File"); file_btn.clicked.connect(lambda checked=False,f=file:self.show_file(f)); line.addWidget(name); line.addWidget(play); line.addWidget(wave,1); line.addWidget(stop); line.addWidget(file_btn); self.layout.addLayout(line); self.loader.request(file)
    def _wave_ready(self,path,peaks):
        if path in self.waveforms:self.waveforms[path].set_peaks(peaks)
    def _play_solo(self,player):
        for p,_ in self.players:
            if p is not player:p.stop()
        player.setPosition(0); player.play()
    def _play_all(self,row):
        group=self.groups.get(row,[])
        for p,_ in group:p.stop();p.setPosition(0)
        # Queue all starts into the same Qt event-loop turn for the tightest sync QMediaPlayer provides.
        QTimer.singleShot(0,lambda:[p.play() for p,_ in group])
    def _pause_all(self,row):
        for p,_ in self.groups.get(row,[]):p.pause()
    def _stop_all(self,row):
        for p,_ in self.groups.get(row,[]):p.stop();p.setPosition(0)
    @staticmethod
    def show_file(file):
        if sys.platform=="win32":subprocess.Popen(["explorer","/select,",str(Path(file))])
        else:StemResults.open_folder(str(Path(file).parent))
    @staticmethod
    def open_folder(folder):
        if sys.platform=="win32":os.startfile(folder)
        elif sys.platform=="darwin":subprocess.Popen(["open",folder])
        else:subprocess.Popen(["xdg-open",folder])
