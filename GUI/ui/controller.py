"""Backend adapter for the modern Demucs Studio UI."""
import pathlib
import threading

import separator
import shared


class StudioController:
    def __init__(self, window):
        self.window = window
        self.engine = None
        self.device = "cpu"
        self.busy = False
        separator.setUpdateStatusFunc(window.statusChanged.emit)

    def initialize(self):
        def ready(_paused=0, error=""):
            if error:
                self.window.errorRaised.emit("Startup failed", error)
                return
            try:
                devices = separator.getAvailableDevices()
                if devices:
                    idx = min(separator.default_device, len(devices)-1)
                    self.device = devices[idx][1]
                    self.window.deviceChanged.emit(devices[idx][0])
                self.window.backendReady.emit()
            except Exception as exc:
                self.window.errorRaised.emit("Device detection failed", str(exc))
        separator.starter(self.window.statusChanged.emit, ready)

    def load_model_and_start(self, model, files):
        if self.busy or not files:
            return
        self.busy = True
        self.window.busyChanged.emit(True)

        def work():
            try:
                self.engine = separator.DemucsSeparator()
                # Populate remote URL metadata used by ensureDownloaded().
                models, _, _ = self.engine.listModels()
                if model not in models:
                    raise RuntimeError(f"Demucs model '{model}' is not available")
                self.window.statusChanged.emit(f"Loading model: {model}")
                self.engine.loadModel(model)
                self._files = list(files)
                self._index = 0
                self._run_next()
            except Exception as exc:
                self.busy = False
                self.window.busyChanged.emit(False)
                self.window.errorRaised.emit("Unable to start separation", str(exc))
        threading.Thread(target=work, daemon=True).start()

    def _run_next(self):
        if self._index >= len(self._files):
            self.busy = False
            self.window.busyChanged.emit(False)
            self.window.statusChanged.emit("Separation complete")
            self.window.allFinished.emit()
            separator.empty_cache()
            return
        path = pathlib.Path(self._files[self._index])
        row = self._index
        self.window.trackStarted.emit(row, path.name)
        segment = min(float(getattr(self.engine, "default_segment", 7.8)), float(getattr(self.engine, "max_segment", 7.8)))
        self.engine.startSeparate(path, row, 0.0, segment, 0.25, 1, self.device,
            self._save, self.window.modelProgress.emit,
            lambda value, item: self.window.trackProgress.emit(int(item), value),
            lambda status, item: self.window.trackStatus.emit(int(item), int(status)),
            self._finished)

    def _save(self, file, origin, tensor, tags, save_func, item, finish_callback):
        try:
            out_dir = file.parent / "separated" / self.engine.model / file.stem
            out_dir.mkdir(parents=True, exist_ok=True)
            for stem, data in tensor.items():
                output = out_dir / f"{stem}.wav"
                result = save_func(output, data, "PCM_24", encoder="sndfile")
                if result is not None:
                    raise RuntimeError(str(result))
            finish_callback(shared.FileStatus.Finished, item)
        except Exception:
            finish_callback(shared.FileStatus.Failed, item)

    def _finished(self, status, item):
        self.window.trackFinished.emit(int(item), int(status))
        if status == shared.FileStatus.Finished:
            self._index += 1
            self._run_next()
        else:
            self.busy = False
            self.window.busyChanged.emit(False)
