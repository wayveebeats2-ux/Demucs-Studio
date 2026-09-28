"""Fast local metadata extraction for queue presentation."""
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool
import tinytag

class _TaskSignals(QObject):
    ready=Signal(str,dict)

class _Task(QRunnable):
    def __init__(self,path): super().__init__(); self.path=path; self.signals=_TaskSignals()
    def run(self):
        p=Path(self.path); info={"name":p.name,"size":p.stat().st_size if p.exists() else 0}
        try:
            tag=tinytag.TinyTag.get(str(p),image=True)
            info.update({"duration":float(tag.duration or 0),"title":tag.title or p.stem,"artist":tag.artist or "","album":tag.album or ""})
            image=tag.get_image()
            if image: info["artwork"]=bytes(image)
        except Exception:
            info.update({"duration":0.0,"title":p.stem,"artist":"","album":""})
        self.signals.ready.emit(self.path,info)

class MediaInfoLoader(QObject):
    ready=Signal(str,dict)
    def __init__(self,parent=None): super().__init__(parent); self.pool=QThreadPool.globalInstance(); self._tasks=[]
    def request(self,path):
        task=_Task(path); task.signals.ready.connect(self.ready); self._tasks.append(task); self.pool.start(task)
