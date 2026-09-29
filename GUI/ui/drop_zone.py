from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class DropZone(QFrame):
    filesDropped = Signal(list)
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(170)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("DROP TRACKS HERE")
        title.setObjectName("accent")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("or click Add Tracks  •  WAV, FLAC, MP3 and other FFmpeg-supported audio")
        hint.setObjectName("muted")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(title)
        layout.addWidget(hint)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setProperty("dragActive", True)
            self.style().unpolish(self); self.style().polish(self)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: event.ignore()

    def dragLeaveEvent(self, event):
        self._reset_drag()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._reset_drag()
        paths = [str(Path(u.toLocalFile())) for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.filesDropped.emit(paths)
        event.acceptProposedAction()

    def _reset_drag(self):
        self.setProperty("dragActive", False)
        self.style().unpolish(self); self.style().polish(self)
