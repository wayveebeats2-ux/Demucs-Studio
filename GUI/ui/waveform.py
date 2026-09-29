"""Real audio waveform preview widgets for completed stems."""
import numpy as np
import soundfile as sf
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor
from PySide6.QtWidgets import QWidget

class _Signals(QObject):
    ready=Signal(str,object)

class _WaveTask(QRunnable):
    def __init__(self,path,points=420): super().__init__(); self.path=path; self.points=points; self.signals=_Signals()
    def run(self):
        try:
            data,_=sf.read(self.path,dtype="float32",always_2d=True)
            mono=np.max(np.abs(data),axis=1)
            if len(mono)>self.points:
                edges=np.linspace(0,len(mono),self.points+1,dtype=int)
                peaks=np.array([mono[edges[i]:edges[i+1]].max(initial=0) for i in range(self.points)],dtype=np.float32)
            else: peaks=mono.astype(np.float32)
            peak=float(peaks.max(initial=0));
            if peak>0: peaks/=peak
            self.signals.ready.emit(self.path,peaks)
        except Exception: self.signals.ready.emit(self.path,np.zeros(1,dtype=np.float32))

class WaveformLoader(QObject):
    ready=Signal(str,object)
    def __init__(self,parent=None): super().__init__(parent); self.pool=QThreadPool.globalInstance(); self.tasks=[]
    def request(self,path):
        task=_WaveTask(path); task.signals.ready.connect(self.ready); self.tasks.append(task); self.pool.start(task)

class WaveformWidget(QWidget):
    seekRequested=Signal(float)
    expandRequested=Signal()
    def __init__(self,parent=None): super().__init__(parent); self.peaks=None; self.progress=0.0; self.setMinimumWidth(150); self.setFixedHeight(38); self.setCursor(Qt.CursorShape.PointingHandCursor)
    def set_peaks(self,peaks): self.peaks=peaks; self.update()
    def set_progress(self,value): self.progress=max(0.0,min(1.0,float(value))); self.update()
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.width()>0:self.seekRequested.emit(event.position().x()/self.width())
        super().mousePressEvent(event)
    def mouseDoubleClickEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:self.expandRequested.emit();event.accept();return
        super().mouseDoubleClickEvent(event)
    def contextMenuEvent(self,event):
        from PySide6.QtWidgets import QMenu
        menu=QMenu(self); action=menu.addAction("Expand Waveform")
        if menu.exec(event.globalPos())==action:self.expandRequested.emit()
    def mouseMoveEvent(self,event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.width()>0:self.seekRequested.emit(event.position().x()/self.width())
        super().mouseMoveEvent(event)
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); mid=self.height()/2
        p.setPen(QPen(QColor("#2c3546"),1)); p.drawLine(0,int(mid),self.width(),int(mid))
        if self.peaks is None or len(self.peaks)==0:return
        path=QPainterPath(); n=len(self.peaks); xscale=self.width()/max(1,n-1); amp=max(2,mid-3)
        for i,v in enumerate(self.peaks):
            x=i*xscale; y=amp*float(v); path.moveTo(x,mid-y); path.lineTo(x,mid+y)
        p.setPen(QPen(QColor("#9b6cff"),1)); p.drawPath(path)
        x=int(self.progress*max(0,self.width()-1)); p.setPen(QPen(QColor("#f4f7ff"),2)); p.drawLine(x,2,x,self.height()-2)
