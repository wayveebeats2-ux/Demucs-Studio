"""Persistent index for completed Demucs Studio separations."""
import json
from datetime import datetime
from pathlib import Path
import shared

def _path():
    base=Path(getattr(shared,"config_path",Path.home()/".demucs-studio"))
    base.mkdir(parents=True,exist_ok=True)
    return base/"studio_library.json"

def load():
    try:
        data=json.loads(_path().read_text(encoding="utf-8"))
        return data if isinstance(data,list) else []
    except (FileNotFoundError,json.JSONDecodeError,OSError):
        return []

def save(items):
    _path().write_text(json.dumps(items,indent=2,ensure_ascii=False),encoding="utf-8")

def add(source,folder,model,preset,outputs,metadata=None):
    items=load(); key=str(Path(folder).resolve()).lower()
    entry={"source":str(source),"folder":str(folder),"model":model,"preset":preset,
           "outputs":[[a,b] for a,b in outputs],"metadata":metadata or {},
           "created":datetime.now().isoformat(timespec="seconds")}
    items=[x for x in items if str(Path(x.get("folder","")).resolve()).lower()!=key]
    items.insert(0,entry); save(items); return entry

def scan(root):
    root=Path(root); items=load(); known={str(Path(x.get("folder","")).resolve()).lower() for x in items}; added=0
    names={"vocals","drums","bass","other","guitar","piano"}
    for d in [p for p in root.rglob("*") if p.is_dir()]:
        wavs=[p for p in d.glob("*.wav") if p.stem.lower().split("_")[0] in names]
        if len(wavs)>=2 and str(d.resolve()).lower() not in known:
            outputs=[(p.stem,p.as_posix()) for p in wavs]
            model=d.parent.name; items.append({"source":"","folder":str(d),"model":model,"preset":"imported","outputs":outputs,"metadata":{},"created":datetime.now().isoformat(timespec="seconds")}); known.add(str(d.resolve()).lower()); added+=1
    if added:save(items)
    return added
