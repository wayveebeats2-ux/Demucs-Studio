import os,sys,subprocess
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput,QMediaPlayer
from PySide6.QtWidgets import QFrame,QHBoxLayout,QLabel,QPushButton,QVBoxLayout
from ui.waveform import WaveformLoader,WaveformWidget

class StemResults(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent); self.setObjectName("panel"); self.output_dir=None; self.players=[]; self.waveforms={}; self.loader=WaveformLoader(self); self.loader.ready.connect(self._wave_ready)
        self.layout=QVBoxLayout(self); title=QLabel("♫  RESULTS"); title.setObjectName("section"); self.layout.addWidget(title); self.hint=QLabel("Completed stems will appear here."); self.hint.setObjectName("muted"); self.layout.addWidget(self.hint)
    def show_results(self,row,folder,outputs):
        self.output_dir=folder; self.hint.hide(); divider=QFrame(); divider.setFrameShape(QFrame.Shape.HLine); self.layout.addWidget(divider)
        head=QHBoxLayout(); label=QLabel("✓  "+Path(folder).parent.name); label.setObjectName("success"); open_btn=QPushButton("Open Folder"); open_btn.clicked.connect(lambda:self.open_folder(folder)); head.addWidget(label); head.addStretch(); head.addWidget(open_btn); self.layout.addLayout(head)
        for stem,file in outputs:
            line=QHBoxLayout(); name=QLabel("●  "+stem.title()); name.setObjectName("accent"); name.setMinimumWidth(95); wave=WaveformWidget(); self.waveforms[file]=wave
            play=QPushButton("▶"); play.setToolTip("Play stem"); stop=QPushButton("■"); stop.setToolTip("Stop playback"); audio=QAudioOutput(self); player=QMediaPlayer(self); player.setAudioOutput(audio); player.setSource(QUrl.fromLocalFile(file)); self.players.append((player,audio)); play.clicked.connect(lambda checked=False,p=player:self._play_solo(p)); stop.clicked.connect(player.stop)
            file_btn=QPushButton("Show File"); file_btn.clicked.connect(lambda checked=False,f=file:self.show_file(f)); line.addWidget(name); line.addWidget(play); line.addWidget(wave,1); line.addWidget(stop); line.addWidget(file_btn); self.layout.addLayout(line); self.loader.request(file)
    def _wave_ready(self,path,peaks):
        if path in self.waveforms:self.waveforms[path].set_peaks(peaks)
    def _play_solo(self,player):
        for p,_ in self.players:
            if p is not player:p.stop()
        player.play()
    @staticmethod
    def show_file(file):
        if sys.platform=="win32":subprocess.Popen(["explorer","/select,",str(Path(file))])
        else:StemResults.open_folder(str(Path(file).parent))
    @staticmethod
    def open_folder(folder):
        if sys.platform=="win32":os.startfile(folder)
        elif sys.platform=="darwin":subprocess.Popen(["open",folder])
        else:subprocess.Popen(["xdg-open",folder])
