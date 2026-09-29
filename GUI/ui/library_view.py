"""Library browser for previous separations."""
from pathlib import Path
from PySide6.QtCore import Qt,Signal
from PySide6.QtWidgets import QFrame,QHBoxLayout,QLabel,QLineEdit,QListWidget,QListWidgetItem,QPushButton,QVBoxLayout,QFileDialog
from ui import library_store

class LibraryView(QFrame):
    openSession=Signal(dict)
    def __init__(self,parent=None):
        super().__init__(parent); self.setObjectName("panel")
        v=QVBoxLayout(self); top=QHBoxLayout(); title=QLabel("LIBRARY"); title.setObjectName("section"); self.search=QLineEdit(); self.search.setPlaceholderText("Search separations…"); scan=QPushButton("Scan Folder"); refresh=QPushButton("Refresh")
        top.addWidget(title); top.addStretch(); top.addWidget(self.search); top.addWidget(scan); top.addWidget(refresh); v.addLayout(top)
        self.list=QListWidget(); self.list.itemDoubleClicked.connect(self._open); v.addWidget(self.list,1)
        hint=QLabel("Double-click a separation to reopen its synchronized stem player."); hint.setObjectName("muted"); v.addWidget(hint)
        self.search.textChanged.connect(self.reload); scan.clicked.connect(self.scan_folder); refresh.clicked.connect(self.reload); self.reload()
    def reload(self,*_):
        q=self.search.text().strip().lower(); self.list.clear()
        for entry in library_store.load():
            meta=entry.get("metadata") or {}; title=meta.get("title") or Path(entry.get("folder","")).name; artist=meta.get("artist") or "Unknown artist"; outputs=entry.get("outputs",[]); missing=not Path(entry.get("folder","")).exists()
            hay=f"{title} {artist} {entry.get('model','')} {entry.get('folder','')}".lower()
            if q and q not in hay:continue
            text=f"{'⚠' if missing else '♫'}  {title}  •  {artist}\n    {len(outputs)} stems  •  {entry.get('model','Unknown model')}  •  {entry.get('created','').replace('T',' ')}"
            item=QListWidgetItem(text); item.setData(Qt.ItemDataRole.UserRole,entry); item.setToolTip(entry.get("folder","")); self.list.addItem(item)
    def _open(self,item):
        entry=item.data(Qt.ItemDataRole.UserRole)
        if entry:self.openSession.emit(entry)
    def scan_folder(self):
        folder=QFileDialog.getExistingDirectory(self,"Scan for existing separations")
        if folder:library_store.scan(folder);self.reload()
