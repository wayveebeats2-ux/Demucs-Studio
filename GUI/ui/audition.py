"""Live multistem audition engine with synchronized Qt media players."""
from pathlib import Path
import numpy as np
import soundfile as sf
from PySide6.QtCore import QObject,Signal,QUrl,QTimer
from PySide6.QtMultimedia import QAudioOutput,QMediaPlayer

class AuditionMixer(QObject):
    ready=Signal(int); failed=Signal(int,str); positionChanged=Signal("qlonglong"); durationChanged=Signal("qlonglong"); playingChanged=Signal(bool)
    def __init__(self,parent=None):
        super().__init__(parent); self.players={}; self.outputs={}; self.stems=[]; self.state={}; self.key=None; self._duration=0; self._syncing=False
        self._clock=QTimer(self); self._clock.setInterval(80); self._clock.timeout.connect(self._tick)
    def load(self,key,stems,state):
        self.stop(); self._dispose(); self.key=key; self.stems=list(stems); self.state=state
        try:
            durations=[]
            for name,path in self.stems:
                player=QMediaPlayer(self); audio=QAudioOutput(self); player.setAudioOutput(audio); player.setSource(QUrl.fromLocalFile(path))
                self.players[name]=player; self.outputs[name]=audio
                try:
                    info=sf.info(path); durations.append(int(info.frames/info.samplerate*1000))
                except Exception: pass
            self._duration=max(durations) if durations else 0; self.durationChanged.emit(self._duration); self.apply_state(); self.ready.emit(key)
        except Exception as exc:self.failed.emit(key,str(exc))
    def _dispose(self):
        for p in self.players.values():p.stop();p.deleteLater()
        for a in self.outputs.values():a.deleteLater()
        self.players.clear();self.outputs.clear()
    def apply_state(self):
        soloed={k for k,v in self.state.items() if v.get("solo")}
        for name,audio in self.outputs.items():
            cfg=self.state.get(name,{})
            active=(name in soloed) if soloed else not cfg.get("mute",False)
            db=float(cfg.get("db",0.0)); volume=0.0 if not active else min(1.0,max(0.0,10**(db/20.0)))
            audio.setVolume(volume)
    def play_pause(self):
        if not self.players:return
        any_playing=any(p.playbackState()==QMediaPlayer.PlaybackState.PlayingState for p in self.players.values())
        if any_playing:self.pause()
        else:self.play()
    def play(self):
        if not self.players:return
        pos=self.position()
        for p in self.players.values():
            p.setPosition(pos);p.play()
        self._clock.start();self.playingChanged.emit(True)
    def pause(self):
        for p in self.players.values():p.pause()
        self._clock.stop();self.playingChanged.emit(False)
    def stop(self):
        for p in self.players.values():p.stop();p.setPosition(0)
        self._clock.stop();self.positionChanged.emit(0);self.playingChanged.emit(False)
    def seek(self,ms):
        ms=max(0,min(int(ms),self._duration))
        for p in self.players.values():p.setPosition(ms)
        self.positionChanged.emit(ms)
    def position(self):
        if not self.players:return 0
        vals=[p.position() for p in self.players.values()]
        return max(vals) if vals else 0
    def _tick(self):
        if not self.players:return
        pos=self.position(); self.positionChanged.emit(pos)
        if self._duration and pos>=self._duration-100:
            self.stop()
    def export(self,key,stems,state,target,callback=None):
        try:
            loaded=[]; sr=None; maxlen=0; soloed={k for k,v in state.items() if v.get("solo")}
            for name,path in stems:
                cfg=state.get(name,{}); active=(name in soloed) if soloed else not cfg.get("mute",False)
                if not active:continue
                data,rate=sf.read(path,dtype="float32",always_2d=True)
                if sr is None:sr=rate
                if rate!=sr:raise RuntimeError("Stem sample rates do not match")
                data*=10**(float(cfg.get("db",0.0))/20.0);loaded.append(data);maxlen=max(maxlen,len(data))
            if not loaded:raise RuntimeError("No stems are active")
            channels=max(x.shape[1] for x in loaded);mix=np.zeros((maxlen,channels),dtype=np.float32)
            for data in loaded:
                if data.shape[1]==1 and channels>1:data=np.repeat(data,channels,axis=1)
                mix[:len(data)]+=data
            peak=float(np.max(np.abs(mix),initial=0))
            if peak>0.999:mix*=0.999/peak
            sf.write(Path(target),mix,sr,subtype="PCM_24")
            if callback:callback(str(target))
        except Exception as exc:self.failed.emit(key,str(exc))
