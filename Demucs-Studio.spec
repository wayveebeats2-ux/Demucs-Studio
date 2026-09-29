# Demucs Studio portable Windows build (PyInstaller onedir)
from pathlib import Path
root=Path(SPECPATH)
datas=[(str(root/"assets"),"assets")]
hiddenimports=["PySide6.QtMultimedia","soundfile","demucs.api","demucs.apply"]
a=Analysis([str(root/"GUI"/"StudioMain.py")],pathex=[str(root/"GUI")],binaries=[],datas=datas,hiddenimports=hiddenimports,hookspath=[],hooksconfig={},runtime_hooks=[],excludes=[],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name="Demucs Studio",debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False,icon=str(root/"assets"/"branding"/"demucs_studio_icon.ico") if (root/"assets"/"branding"/"demucs_studio_icon.ico").exists() else None)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name="Demucs-Studio-v0.1-win64")
