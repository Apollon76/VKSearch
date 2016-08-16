import functools
from PyQt4 import QtGui as qt, QtCore


def scrollable(cls):
    class ScrollableObject(cls):
        def __init__(self, *args, **kwargs):
            super(cls, self).__init__(*args, **kwargs)
            self.scrollArea = qt.QScrollArea()
            self.scrollArea.setWidgetResizable(True)
            self.scrollArea.setWidget(self)

    return ScrollableObject


def clickable(widget):
    class Filter(QtCore.QObject):
        clicked = QtCore.pyqtSignal()

        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QtCore.QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        return True
            return False

    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked


class Atomic:
    def __init__(self, value):
        self.mutex = QtCore.QMutex()
        self.value = value

    def __getattr__(self, name):
        def wrapped(*args, **kwargs):
            self.mutex.lock()
            getattr(self.value, name)(*args, **kwargs)
            self.mutex.unlock()

        return wrapped

    def get(self):
        self.mutex.lock()
        value = self.value
        self.mutex.unlock()
        return value

    def set(self, value):
        self.mutex.lock()
        self.value = value
        self.mutex.unlock()


class Demon(QtCore.QThread):
    def __init__(self, target=None, args=(), kwargs={}):
        super(Demon, self).__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self._stopped = Atomic(True)

    def run(self):
        self._stopped.set(False)
        self.target(self._stopped, *self.args, **self.kwargs)

    def stop(self):
        self._stopped.set(True)
        self.wait()
