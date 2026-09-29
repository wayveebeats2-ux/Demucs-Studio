"""Sample-aligned audition mixer for separated stems."""
import tempfile, uuid
from pathlib import Path
import numpy as np
import soundfile as sf
from PySide6.QtCore import QObject,QRunnable,QThreadPool,Signal,QUrl
from PySide6.QtMultimedia import QAudioOutput,QMediaPlayer

class _MixSignals(QObject):
    ready=Signal(int,str,object); failed=Signal(int,str)
class _MixTask(QRunnable):
    def __init__(self,key,stems,state,target=None,resume=None): super().__init__(); self.key=key; self.stems=stems; self.state=state; self.target=target; self.resume=resume; self.signals=_MixSignals()
    def run(self):
        try:
            loaded=[]; sr=None; maxlen=0
            soloed={k for k,v in self.state.items() if v.get("solo")}
            for name,path in self.stems:
                cfg=self.state.get(name,{}); active=(name in soloed) if soloed else not cfg.get("mute",False)
                if not active: continue
                data,rate=sf.read(path,dtype="float32",always_2d=True)
                if sr is None:sr=rate
                if rate!=sr:raise RuntimeError("Stem sample rates do not match")
                gain=10**(float(cfg.get("db",0.0))/20.0); data=data*gain; loaded.append(data); maxlen=max(maxlen,len(data))
            if not loaded:raise RuntimeError("No stems are active")
            channels=max(x.shape[1] for x in loaded); mix=np.zeros((maxlen,channels),dtype=np.float32)
            for data in loaded:
                if data.shape[1]!=channels:
                    if data.shape[1]==1: data=np.repeat(data,channels,axis=1)
                    else: raise RuntimeError("Stem channel layouts do not match")
                mix[:len(data)]+=data
            peak=float(np.max(np.abs(mix),initial=0));
            if peak>0.999:mix*=0.999/peak
            out=Path(self.target) if self.target else Path(tempfile.gettempdir())/f"demucs_studio_audition_{self.key}_{uuid.uuid4().hex}.wav"; sf.write(out,mix,sr,subtype="PCM_24"); self.signals.ready.emit(self.key,str(out),self.resume)
        except Exception as exc:self.signals.failed.emit(self.key,str(exc))

class AuditionMixer(QObject):
    ready=Signal(int); failed=Signal(int,str); positionChanged=Signal("qlonglong"); durationChanged=Signal("qlonglong"); playingChanged=Signal(bool)
    def __init__(self,parent=None):
        super().__init__(parent); self.pool=QThreadPool.globalInstance(); self.audio=QAudioOutput(self); self.player=QMediaPlayer(self); self.player.setAudioOutput(self.audio); self.tasks=[]; self.player.positionChanged.connect(self.positionChanged); self.player.durationChanged.connect(self.durationChanged); self.player.playbackStateChanged.connect(lambda s:self.playingChanged.emit(s==QMediaPlayer.PlaybackState.PlayingState))
    def render_and_play(self,key,stems,state,resume_position=None,resume_playing=None):
        if resume_position is None: resume_position=self.player.position()
        if resume_playing is None: resume_playing=self.player.playbackState()==QMediaPlayer.PlaybackState.PlayingState
        task=_MixTask(key,stems,state,resume=(int(resume_position),bool(resume_playing))); task.signals.ready.connect(self._play); task.signals.failed.connect(self.failed); self.tasks.append(task); self.pool.start(task)
    def export(self,key,stems,state,target,callback=None):
        task=_MixTask(key,stems,state,target); task.signals.ready.connect(lambda k,p,resume: callback(p) if callback else None); task.signals.failed.connect(self.failed); self.tasks.append(task); self.pool.start(task)
    def _play(self,key,path,resume):
        pos,was_playing=resume or (0,True)
        self.player.stop(); self.player.setSource(QUrl.fromLocalFile(path)); self.player.setPosition(max(0,int(pos)))
        if was_playing:self.player.play()
        else:self.player.pause()
        self.ready.emit(key)
    def play_pause(self):
        if self.player.playbackState()==QMediaPlayer.PlaybackState.PlayingState:self.player.pause()
        else:self.player.play()
    def seek(self,ms):self.player.setPosition(max(0,min(int(ms),self.player.duration())))
    def pause(self):self.player.pause()
    def stop(self):self.player.stop();self.player.setPosition(0)
