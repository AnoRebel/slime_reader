import asyncio
import sys

#  from threading import Thread, Event
import qasync
from qasync import asyncSlot

#  from qasync import asyncSlot, asyncClose, QApplication

try:
    #  from PyQt5 import QtGui, QtWidgets, QtCore, uic
    from PyQt5.QtCore import QCoreApplication, QProcess, Qt
    from PyQt5.QtCore import pyqtSignal as Signal
    from PyQt5.QtCore import pyqtSlot as Slot
    from PyQt5.QtGui import QColor
    from PyQt5.QtWidgets import (
        QApplication,
        QDialog,
        QMessageBox,
        QGraphicsDropShadowEffect,
        QMainWindow,
    )
    from PyQt5.uic import loadUi
except ImportError:
    #  from PySide2 import QtGui, QtWidgets, QtCore
    from PySide2.QtWidgets import (
        QDialog,
        QMainWindow,
        QMessageBox,
        QGraphicsDropShadowEffect,
        QApplication,
    )
    from PySide2.QtCore import (
        pyqtSlot as Slot,
        pyqtSignal as Signal,
        Qt,
        QCoreQCoreApplication,
        QProcess,
    )
    from PySide2.QtGui import QColor
    from PySide2.uic import loadUi

from functools import partial
from typing import Optional
from rich.traceback import install

from Tensura import Tensura

install()

LOCAL = True
ALT = False
APP: Optional[Tensura] = None


class ChapterLink(QDialog):
    loaded = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        loadUi("ChapterLink.ui", self)

        # Remove Titlebar
        self.setWindowFlag(Qt.FramelessWindowHint)

        # Connect signals to slots
        self.cancel_dialog_btn.clicked.connect(self.close)
        self.load_chapter_btn.clicked.connect(self.loadChapter)

    def loadChapter(self) -> None:
        link = self.linkInput.text()
        self.loaded.emit(link)
        self.close()


class AboutDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        loadUi("AboutDialog.ui", self)

        # Remove Titlebar
        self.setWindowFlag(Qt.FramelessWindowHint)

        # DropShadow Effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.frame.setGraphicsEffect(self.shadow)

        # Connect signals to slots
        self.dismiss_btn.clicked.connect(self.close)


class TensuraReader(QMainWindow):
    def __init__(self, local: bool, alt: bool) -> None:
        super().__init__()
        loadUi("TensuraReader.ui", self)
        #  self.reader = await Tensura()
        self.connectSignals()
        self.local = local
        self.alt = alt
        #  self.statusbar.showMessage("Launched.", 2000)
        self.statusbar.showMessage(f"{self.alt}: {self.local}")
        global APP
        APP = Tensura(local=self.local, alt=self.alt)

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
        if APP is not None:
            if self.alt:
                self.chapter_select.addItem("None Provided")
                self.chapter_select.setFrame(False)
            else:
                self.chapter_select.addItems(APP.chapters)

    def configureChapterContent(self) -> None:
        #  self.chapter_content
        pass

    @asyncSlot(str)
    async def linkLoaded(self, link):
        if APP is not None:
            await APP.crawl(link)
            self.dlg.close()
        else:
            QMessageBox.critical(self, "App Error", "App not initialized properly.")

    def loadLink(self) -> None:
        self.dlg = ChapterLink()
        self.dlg.show()
        self.dlg.loaded.connect(self.linkLoaded)

    @Slot()
    def openAbout(self) -> None:
        self.about = AboutDialog()
        self.about.show()

    @Slot()
    def loadChapter(self) -> None:
        #  tmp = self.chapter_select
        pass

    @Slot()
    def on_prev(self) -> None:
        pass

    @Slot()
    def on_next(self) -> None:
        pass

    @Slot()
    def on_stop(self) -> None:
        pass

    @Slot()
    def togglePlayPause(self) -> None:
        #  self.toggle_play_btn
        pass


class SlimeReader(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        loadUi("SlimeReader.ui", self)

        # Fix Bg Image
        self.frame.setStyleSheet(
            "QFrame {\n"
            "    border-radius: 6px;\n"
            "    background-color: rgb(20, 20, 20);\n"
            "    background-image: url(assets/tensura.jpg);\n"
            "}"
        )

        # Remove Titlebar
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # DropShadow Effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.frame.setGraphicsEffect(self.shadow)

        # Connect the buttons to functions
        self.online.setChecked(True)
        self.exit_btn.clicked.connect(self.close)
        self.ok_btn.clicked.connect(self.on_ok)

    @Slot()
    def on_ok(self) -> None:
        global LOCAL, ALT
        ALT = self.site_select.currentIndex()
        LOCAL = (
            True
            if (self.online.isChecked() and not self.offline.isChecked())
            else False
        )
        self.main = TensuraReader(LOCAL, bool(ALT))
        self.close()
        self.main.show()


def restart() -> None:
    QCoreApplication.quit()
    QProcess.startDetached(sys.executable, sys.argv)


async def main():
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    loop = asyncio.get_event_loop()
    future = asyncio.Future()
    app = QApplication.instance()
    if hasattr(app, "aboutToQuit"):
        getattr(app, "aboutToQuit").connect(partial(close_future, future, loop))
    window = SlimeReader()
    window.show()
    await future
    return True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SlimeReader()
    window.show()
    sys.exit(app.exec())
    try:
        qasync.run(main())
    except asyncio.exceptions.CancelledError:
        sys.exit(0)
