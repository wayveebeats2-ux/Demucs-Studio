"""Backend adapter for the modern Demucs Studio UI."""
import pathlib, threading
import separator, shared
from ui import library_store

class StudioController:
    def __init__(self, window):
        self.window=window; self.engine=None; self.device="cpu"; self.busy=False
        separator.setUpdateStatusFunc(window.statusChanged.emit)
    def initialize(self):
        def ready(_paused=0,error=""):
            if error: self.window.errorRaised.emit("Startup failed",error); return
            try:
                devices=separator.getAvailableDevices()
                if devices:
                    idx=min(separator.default_device,len(devices)-1); self.device=devices[idx][1]; self.window.deviceChanged.emit(devices[idx][0])
                self.window.backendReady.emit()
            except Exception as exc: self.window.errorRaised.emit("Device detection failed",str(exc))
        separator.starter(self.window.statusChanged.emit,ready)
    def load_model_and_start(self,model,files,options=None):
        if self.busy or not files:return
        self.options=options or {}; self.busy=True; self.window.busyChanged.emit(True)
        def work():
            try:
                self.engine=separator.DemucsSeparator(); models,_,_=self.engine.listModels()
                if model not in models: raise RuntimeError(f"Demucs model '{model}' is not available")
                self.window.statusChanged.emit(f"Loading model: {model}"); self.engine.loadModel(model)
                self._files=list(files); self._index=0; self._run_next()
            except Exception as exc:
                self.busy=False; self.window.busyChanged.emit(False); self.window.errorRaised.emit("Unable to start separation",str(exc))
        threading.Thread(target=work,daemon=True).start()
    def _run_next(self):
        if self._index>=len(self._files):
            self.busy=False; self.window.busyChanged.emit(False); self.window.statusChanged.emit("Separation complete"); self.window.allFinished.emit(); separator.empty_cache(); return
        path=pathlib.Path(self._files[self._index]); row=self._index; self.window.trackStarted.emit(row,path.name)
        default=min(float(getattr(self.engine,"default_segment",7.8)),float(getattr(self.engine,"max_segment",7.8)))
        segment=min(float(self.options.get("segment",default)),float(getattr(self.engine,"max_segment",default)))
        overlap=float(self.options.get("overlap",0.25)); shifts=int(self.options.get("shifts",1)); gain=float(self.options.get("gain",0.0))
        self.engine.startSeparate(path,row,gain,segment,overlap,shifts,self.device,self._save,self.window.modelProgress.emit,
            lambda value,item:self.window.trackProgress.emit(int(item),value),lambda status,item:self.window.trackStatus.emit(int(item),int(status)),self._finished)
    def _save(self,file,origin,tensor,tags,save_func,item,finish_callback):
        try:
            base=self.options.get("output_dir")
            out_dir=(pathlib.Path(base)/self.engine.model/file.stem) if base else (file.parent/"separated"/self.engine.model/file.stem)
            out_dir.mkdir(parents=True,exist_ok=True); outputs=[]; policy=self.options.get("collision","rename")
            subtype=self.options.get("subtype","PCM_24")
            for stem,data in tensor.items():
                output=out_dir/f"{stem}.wav"
                if output.exists():
                    if policy=="skip": outputs.append((stem,str(output))); continue
                    if policy=="rename":
                        n=2
                        while (out_dir/f"{stem}_{n}.wav").exists(): n+=1
                        output=out_dir/f"{stem}_{n}.wav"
                result=save_func(output,data,subtype,encoder="sndfile")
                if result is not None: raise RuntimeError(str(result))
                outputs.append((stem,str(output)))
            metadata={}
            try:
                qitem=self.window.queue.item(int(item)); metadata=qitem.data(257) or {}
            except Exception: pass
            library_store.add(str(file),str(out_dir),self.engine.model,self.options.get("preset","four"),outputs,metadata)
            self.window.resultsReady.emit(int(item),str(out_dir),outputs); self.window.libraryChanged.emit(); finish_callback(shared.FileStatus.Finished,item)
        except Exception as exc:
            self.window.errorRaised.emit("Failed to save stems",str(exc)); finish_callback(shared.FileStatus.Failed,item)
    def _finished(self,status,item):
        self.window.trackFinished.emit(int(item),int(status))
        if status==shared.FileStatus.Finished: self._index+=1; self._run_next()
        else: self.busy=False; self.window.busyChanged.emit(False)
