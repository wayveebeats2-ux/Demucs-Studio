import os, sys, subprocess
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QFrame,QHBoxLayout,QLabel,QPushButton,QVBoxLayout

class StemResults(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent); self.setObjectName("panel"); self.output_dir=None; self.players=[]
        self.layout=QVBoxLayout(self); title=QLabel("RESULTS"); title.setObjectName("accent"); self.layout.addWidget(title)
        self.hint=QLabel("Completed stems will appear here."); self.hint.setObjectName("muted"); self.layout.addWidget(self.hint)
    def show_results(self,row,folder,outputs):
        self.output_dir=folder; self.hint.hide()
        head=QHBoxLayout(); label=QLabel(Path(folder).parent.name); label.setObjectName("accent"); open_btn=QPushButton("Open Folder"); open_btn.clicked.connect(lambda:self.open_folder(folder)); head.addWidget(label); head.addStretch(); head.addWidget(open_btn); self.layout.addLayout(head)
        for stem,file in outputs:
            line=QHBoxLayout(); name=QLabel(stem.upper()); play=QPushButton("▶ Play"); stop=QPushButton("■ Stop")
            audio=QAudioOutput(self); player=QMediaPlayer(self); player.setAudioOutput(audio); player.setSource(QUrl.fromLocalFile(file)); self.players.append((player,audio))
            play.clicked.connect(lambda checked=False,p=player:self._play_solo(p)); stop.clicked.connect(player.stop)
            line.addWidget(name); line.addStretch(); line.addWidget(play); line.addWidget(stop); self.layout.addLayout(line)
    def _play_solo(self,player):
        for p,_ in self.players:
            if p is not player:p.stop()
        player.play()
    @staticmethod
    def open_folder(folder):
        if sys.platform=="win32": os.startfile(folder)
        elif sys.platform=="darwin": subprocess.Popen(["open",folder])
        else: subprocess.Popen(["xdg-open",folder])
