import sys
import time
import asyncio
import threading
#  from threading import Thread, Event
import qasync

try:
    from PyQt5 import QtGui, QtWidgets, QtCore, uic
except ImportError:
    from PySide2 import QtGui, QtWidgets, QtCore

from rich.traceback import install
from Tensura import Tensura

install()

URL = 1
ALT = True


class setInterval:
    """
    A python version of a setInterval class that allows running functions at an
    interval and cancelling them

    Attributes
    ----------
    interval: `float`
        The time interval in seconds to rerun the given action
    action: `Function`
        An action to be run and rerun after given seconds interval

    Usage
    -----
    `py
    interval = setInterval(seconds, function)
    t = threading.Timer(seconds, inter.cancel)
    t.start()
    `
    """

    def __init__(self, interval, action) -> None:
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self) -> None:
        """
        Custom method to run a function every given seconds
        """
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self) -> None:
        """
        Stops the current running loop
        """
        self.stopEvent.set()


class ChapterLink(QtWidgets.QDialog):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("ChapterLink.ui", self)

        # Remove Titlebar
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        # Connect signals to slots
        self.cancel_dialog_btn.clicked.connect(self.close)
        #  self.load_chapter_btn.clicked.connect()

        @QtCore.pyqtSlot()
        def loadChapter(self) -> None:
            #  tmp = self.linkInput
            pass


class AboutDialog(QtWidgets.QDialog):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("AboutDialog.ui", self)

        # Remove Titlebar
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)

        # DropShadow Effect
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QtGui.QColor(0, 0, 0, 60))
        self.frame.setGraphicsEffect(self.shadow)

        # Connect signals to slots
        self.dismiss_btn.clicked.connect(self.close)


class TensuraReader(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("TensuraReader.ui", self)
        #  self.reader = await Tensura()
        self.connectSignals()
        self.statusbar.showMessage("Launched.", 2000)

    def connectSignals(self) -> None:
        # Actions
        self.action_Restart.triggered.connect(restart)
        self.action_Quit.triggered.connect(self.close)
        self.action_LoadLink.triggered.connect(self.loadLink)
        self.action_About.triggered.connect(self.openAbout)
        # Buttons
        self.load_btn.clicked.connect(self.loadChapter)
        self.prev_btn.clicked.connect(self.on_prev)
        self.toggle_play_btn.clicked.connect(self.togglePlayPause)
        self.stop_btn.clicked.connect(self.on_stop)
        self.next_btn.clicked.connect(self.on_next)

    def configureChapterSelect(self) -> None:
        #  self.chapter_select
        pass

    def configureChapterContent(self) -> None:
        #  self.chapter_content
        pass

    @QtCore.pyqtSlot()
    def loadLink(self) -> None:
        self.dlg = ChapterLink()
        self.dlg.show()

    @QtCore.pyqtSlot()
    def openAbout(self) -> None:
        self.about = AboutDialog()
        self.about.show()

    @QtCore.pyqtSlot()
    def loadChapter(self) -> None:
        #  tmp = self.chapter_select
        pass

    @QtCore.pyqtSlot()
    def on_prev(self) -> None:
        pass

    @QtCore.pyqtSlot()
    def on_next(self) -> None:
        pass

    @QtCore.pyqtSlot()
    def on_stop(self) -> None:
        pass

    @QtCore.pyqtSlot()
    def togglePlayPause(self) -> None:
        #  self.toggle_play_btn
        pass


class SlimeReader(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("SlimeReader.ui", self)

        # Fix Bg Image
        self.frame.setStyleSheet(
            "QFrame {\n"
            "    border-radius: 6px;\n"
            "    background-color: rgb(20, 20, 20);\n"
            "    background-image: url(assets/tensura.jpg);\n"
            "}"
        )

        # Remove Titlebar
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # DropShadow Effect
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QtGui.QColor(0, 0, 0, 60))
        self.frame.setGraphicsEffect(self.shadow)

        # Connect the buttons to functions
        self.online.setChecked(True)
        self.exit_btn.clicked.connect(self.close)
        self.ok_btn.clicked.connect(self.on_ok)

    @QtCore.pyqtSlot()
    def on_ok(self) -> None:
        global URL, ALT
        URL = self.site_select.currentIndex()
        ALT = (
            True
            if (self.online.isChecked() and not self.offline.isChecked())
            else False
        )
        self.main = TensuraReader()
        self.close()
        self.main.show()


def restart() -> None:
    QtCore.QCoreApplication.quit()
    QtCore.QProcess.startDetached(sys.executable, sys.argv)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = SlimeReader()
    window.show()
    sys.exit(app.exec())
