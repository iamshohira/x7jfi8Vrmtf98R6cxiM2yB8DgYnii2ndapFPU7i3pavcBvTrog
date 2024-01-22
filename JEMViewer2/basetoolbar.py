from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import JEMViewer2.stylesheet as ss
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class BaseToolbar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(ss.toolbutton)
        self.actions = {}
        dummybar = NavigationToolbar(FigureCanvas(), None)
        for text, tooltip_text, image_file, callback, rightcallback, checkable in self.toolitems:
            if text is None:
                self.addSeparator()
            else:
                a = self.addCAction(dummybar._icon(image_file + '.png'), text, callback, rightcallback)
                self.actions[callback] = a
                a.setCheckable(checkable)
                if tooltip_text is not None:
                    a.setToolTip(tooltip_text)

    def addCAction(self, icon, text, callback, rightcallback):
        b = RightClickToolButton(self)
        b.setIcon(icon)
        b.setText(text)
        b.clicked.connect(getattr(self, callback))
        if rightcallback is not None:
            b.rightClicked.connect(getattr(self, rightcallback))
        self.addWidget(b)
        return b

    def event(self, event):
        if event.type() == QEvent.Type.ContextMenu:
            return True
        return super().event(event)
    
class RightClickToolButton(QToolButton):
    rightClicked = pyqtSignal()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            self.rightClicked.emit()
        else:
            super().mouseReleaseEvent(e)