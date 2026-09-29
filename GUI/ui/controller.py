"""Backend adapter for the modern Demucs Studio UI."""
import pathlib, threading, hashlib, urllib.request, gc
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


    def refine_drums(self,parent_row,drum_file,parent_folder):
        if self.busy:
            self.window.errorRaised.emit("Demucs Studio is busy","Wait for the current separation to finish first."); return
        self.busy=True; self.window.busyChanged.emit(True)
        def work():
            try:
                repo=pathlib.Path(shared.pretrained)/"drumsep"; repo.mkdir(parents=True,exist_ok=True)
                checkpoint=repo/"49469ca8.th"
                expected="aefaa8543c9b9c75e22f5f32b53ab86dfe416457849af1383ff1aef83401423f"
                url="https://github.com/ZFTurbo/Music-Source-Separation-Training/releases/download/v1.0.5/model_drumsep.th"
                valid=False
                if checkpoint.exists():
                    valid=self._sha256(checkpoint)==expected
                if not valid:
                    if checkpoint.exists():checkpoint.unlink()
                    tmp=checkpoint.with_suffix(".th.download")
                    self.window.statusChanged.emit("Downloading DrumSep model (first use)…")
                    urllib.request.urlretrieve(url,tmp)
                    if self._sha256(tmp)!=expected:
                        tmp.unlink(missing_ok=True); raise RuntimeError("Downloaded DrumSep checkpoint failed SHA-256 verification.")
                    tmp.replace(checkpoint)
                self.window.statusChanged.emit("Preparing GPU for DrumSep…")
                # The full-song Demucs model is no longer needed for this second-stage job.
                # Drop it before loading DrumSep so both models do not occupy VRAM together.
                self.engine=None
                if hasattr(self,"_drum_engine"): self._drum_engine=None
                gc.collect(); separator.empty_cache()
                self.window.statusChanged.emit("Loading DrumSep • Kick / Snare / Cymbals / Toms")
                engine=separator.DemucsSeparator(); engine.loadModel("49469ca8",repo=repo); self._drum_engine=engine
                model_default=min(float(getattr(engine,"default_segment",7.8)),float(getattr(engine,"max_segment",7.8)))
                # DrumSep is substantially heavier than the normal 4-stem audition path.
                # A shorter segment trades some speed for much lower peak VRAM usage.
                default=min(model_default,4.0) if str(self.device).lower()!="cpu" else model_default
                out_dir=pathlib.Path(parent_folder)/"drums"
                subrow=-(abs(hash((str(parent_folder),str(drum_file),"drumsep")))%9000000+1000000)
                def save_cb(file,origin,tensor,tags,save_func,item,finish_callback):
                    try:
                        out_dir.mkdir(parents=True,exist_ok=True); outputs=[]; names={"bombo":"kick","redoblante":"snare","platillos":"cymbals","toms":"toms"}
                        for native,data in tensor.items():
                            display=names.get(native,native); output=out_dir/f"{display}.wav"
                            result=save_func(output,data,"PCM_24",encoder="sndfile")
                            if result is not None:raise RuntimeError(str(result))
                            outputs.append((display,str(output)))
                        self.window.drumSubstemsReady.emit(parent_row,outputs)
                        self.window.statusChanged.emit("DrumSep complete • Kick / Snare / Cymbals / Toms")
                        finish_callback(shared.FileStatus.Finished,item)
                    except Exception as exc:
                        self.window.errorRaised.emit("Failed to save DrumSep stems",str(exc)); finish_callback(shared.FileStatus.Failed,item)
                def finished(status,item):
                    self._drum_engine=None; gc.collect(); separator.empty_cache()
                    self.busy=False; self.window.busyChanged.emit(False)
                    if status!=shared.FileStatus.Finished:self.window.errorRaised.emit("DrumSep failed","The drum sub-separation did not complete. If CUDA ran out of memory, close other GPU-heavy apps or use CPU for DrumSep.")
                engine.startSeparate(pathlib.Path(drum_file),subrow,0.0,default,0.25,1,self.device,save_cb,self.window.modelProgress.emit,lambda v,i:None,lambda s,i:None,finished)
            except Exception as exc:
                self.busy=False; self.window.busyChanged.emit(False); self.window.errorRaised.emit("Unable to refine drums",str(exc))
        threading.Thread(target=work,daemon=True).start()

    @staticmethod
    def _sha256(path):
        h=hashlib.sha256()
        with open(path,"rb") as f:
            for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
        return h.hexdigest()
