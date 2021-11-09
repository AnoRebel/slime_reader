import asyncio
import sys

#  from threading import Thread, Event
import qasync
from qasync import QApplication, asyncClose, asyncSlot

#  from qasync import asyncSlot, asyncClose


try:
    #  from PyQt5 import QtGui, QtWidgets, QtCore, uic
    from PyQt5.QtCore import QCoreApplication, QProcess, Qt, QThreadPool
    from PyQt5.QtCore import pyqtSignal as Signal
    from PyQt5.QtCore import pyqtSlot as Slot
    from PyQt5.QtGui import QColor, QIcon, QPixmap
    from PyQt5.QtWidgets import QDialog  # QApplication,
    from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QMainWindow, QMessageBox
    from PyQt5.uic import loadUi
except ImportError:
    #  from PySide2 import QtGui, QtWidgets, QtCore
    from PySide2.QtWidgets import (
        QDialog,
        QMainWindow,
        QMessageBox,
        QGraphicsDropShadowEffect,
        #  QApplication,
    )
    from PySide2.QtCore import (
        pyqtSlot as Slot,
        pyqtSignal as Signal,
        Qt,
        QCoreQCoreApplication,
        QProcess,
        QThreadPool,
    )
    from PySide2.QtGui import QColor, QPixmap, QIcon
    from PySide2.uic import loadUi

from functools import partial
from typing import Optional

from rich.traceback import install

from Tensura import Tensura
from ui import Ui_AboutDialog, Ui_ChapterLinkDialog, Ui_InitialScreen, Ui_TensuraReader

install()

LOCAL: bool = True
ALT: bool = False
APP: Optional[Tensura] = None


class ChapterLink(QDialog):
    loaded = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        loadUi("ui/ChapterLink.ui", self)

        # Remove Titlebar
        self.setWindowFlag(Qt.FramelessWindowHint)

        # Connect signals to slots
        self.cancel_dialog_btn.clicked.connect(self.close)
        self.load_chapter_btn.clicked.connect(self.loadChapter)

    @asyncSlot()
    async def loadChapter(self) -> None:
        link = self.linkInput.text()
        self.load_chapter_btn.setText("Loading...")
        self.load_chapter_btn.setEnabled(False)
        if APP is not None:
            content = await APP.crawl(link)
            self.load_chapter_btn.setText("Load")
            self.load_chapter_btn.setEnabled(True)
            if APP.error:
                msgBox(self, "Network Error", "Failed to load chapter.")
                #  QMessageBox.critical(self, "Network Error", "Failed to load chapter.")
            else:
                self.loaded.emit(content)
                self.close()
        else:
            self.load_chapter_btn.setText("Load")
            self.load_chapter_btn.setEnabled(True)
            msgBox(self, "App Error", "App not initialized properly.", error=True)
            #  QMessageBox.critical(self, "App Error", "App not initialized properly.")


class AboutDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        loadUi("ui/AboutDialog.ui", self)

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
        loadUi("ui/TensuraReader.ui", self)
        #  self.reader = await Tensura()
        self.connectSignals()
        self.local = local
        self.alt = alt
        self.content: str = ""
        self.statusbar.setStyleSheet(
            "QStatusBar {color: rgb(85, 255, 255);background-color: rgb(20, 20,20);}"
        )
        self.threadpool = QThreadPool()
        print(
            f"Multithreading with maximum {str(self.threadpool.maxThreadCount())} threads"
        )
        self.statusbar.showMessage(
            f"Multithreading with maximum {str(self.threadpool.maxThreadCount())} threads",
            2000,
        )
        global APP
        APP = Tensura(local=self.local, alt=self.alt)
        self.origin = APP.BASE_URL_ALT if self.alt else APP.BASE_URL
        self.connectSignals()

    async def init(self):
        if APP is not None:
            self.prev_btn.setEnabled(APP.current_chapter != self.origin)
            self.content = await APP.init()
            if APP.error:
                msgBox(
                    self,
                    "App Error",
                    "Failed to load chapter, please restart app!",
                    error=True,
                )
                #  QMessageBox.critical(
                #  self, "App Error", "Failed to load chapter, please restart app!"
                #  )
            else:
                self.chapter_content.setText(self.content)
                self.setProgress()
                if not self.alt:
                    self.configureChapterSelect()
        else:
            self.statusbar.showMessage("App Error: App not initialized properly.", 5000)
            msgBox(self, "App Error", "App not initialized properly.", error=True)
            #  QMessageBox.critical(self, "App Error", "App not initialized properly.")

    @asyncClose
    async def closeEvent(self, event):
        if APP is not None:
            await APP.session.close()

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
                self.load_btn.setEnabled(False)
                self.chapter_select.clear()
                self.chapter_select.addItem("None Provided")
                self.chapter_select.model().item(0).setEnabled(False)
                #  self.chapter_select.setFrame(False)
            else:
                self.chapter_select.clear()
                self.chapter_select.addItems(list(APP.chapters.keys()))
        else:
            self.statusbar.showMessage("App Error: App not initialized properly.", 5000)
            msgBox(self, "App Error", "App not initialized properly.", error=True)
            #  QMessageBox.critical(self, "App Error", "App not initialized properly.")

    def setChapterContent(self, content: Optional[str] = None) -> None:
        if APP is not None:
            if APP.error:
                QMessageBox.critical(self, "Network Error", "Failed to load chapter.")
                self.statusbar.showMessage("Network Error: Failed to load chapter.")
                self.content = APP.current_chapter_contents
                self.chapter_content.setText(APP.current_chapter_contents)
            else:
                self.chapter_content.setText(content)
        else:
            self.statusbar.showMessage("App Error: App not initialized properly.", 5000)
            msgBox(self, "App Error", "App not initialized properly.", error=True)
            #  QMessageBox.critical(self, "App Error", "App not initialized properly.")

    @Slot(str)
    def linkLoaded(self, content):
        if APP is not None:
            self.content = content
            self.setChapterContent(self.content)
            self.dlg.close()
        else:
            self.statusbar.showMessage("App Error: App not initialized properly.", 5000)
            msgBox(self, "App Error", "App not initialized properly.", error=True)
            #  QMessageBox.critical(self, "App Error", "App not initialized properly.")

    def loadLink(self) -> None:
        self.dlg = ChapterLink()
        self.dlg.show()
        self.dlg.loaded.connect(self.linkLoaded)

    def openAbout(self) -> None:
        self.about = AboutDialog()
        self.about.show()

    @asyncSlot()
    async def loadChapter(self) -> None:
        if APP is not None:
            self.load_btn.setEnabled(False)
            self.load_btn.setText("Loading...")
            key = self.chapter_select.currentText()
            link = APP.chapters[key]
            self.statusbar.showMessage("Loading selected chapter...", 3000)
            self.content = await APP.crawl(link)
            self.statusbar.showMessage("Chapter loaded...", 1000)
            self.setChapterContent(self.content)
            self.setProgress()
            self.load_btn.setText("Load")
            self.load_btn.setEnabled(True)
            self.prev_btn.setEnabled(APP.current_chapter != self.origin)
        else:
            self.statusbar.showMessage("App Error: App not initialized properly.", 5000)
            msgBox(self, "App Error", "App not initialized properly.", error=True)
            #  QMessageBox.critical(self, "App Error", "App not initialized properly")

    @asyncSlot()
    async def on_prev(self) -> None:
        self.prev_btn.setText("Loading...")
        self.prev_btn.setEnabled(False)
        if APP is not None:
            self.statusbar.showMessage("Loading previous chapter...", 3000)
            self.content = await APP.load_prev()
            self.statusbar.showMessage("Chapter loaded.", 1000)
            self.setProgress()
            self.prev_btn.setText("")
            self.prev_btn.setEnabled(True)
            if APP.error:
                msgBox(self, "Network Error", "Failed to laod previous chapter.")
                #  QMessageBox.critical(
                #  self, "Network Error", "Failed to load previous chapter."
                #  )
            else:
                self.chapter_content.setText(self.content)
            self.prev_btn.setEnabled(APP.current_chapter != self.origin)
        else:
            self.prev_btn.setText("")
            self.prev_btn.setEnabled(True)
            self.statusbar.showMessage("App Error: App not initialized properly.", 5000)
            msgBox(self, "App Error", "App not initialized properly.", error=True)
            #  QMessageBox.critical(self, "App Error", "App not initialized properly.")

    @asyncSlot()
    async def on_next(self) -> None:
        self.next_btn.setText("Loading...")
        self.next_btn.setEnabled(False)
        if APP is not None:
            self.statusbar.showMessage("Loading next chapter...", 3000)
            self.content = await APP.load_next()
            self.statusbar.showMessage("Chapter loaded.", 1000)
            self.setProgress()
            self.next_btn.setText("")
            self.next_btn.setEnabled(True)
            if APP.error:
                msgBox(self, "Network Error", "Failed to load next chapter.")
                #  QMessageBox.critical(
                #  self, "Network Error", "Failed to load next chapter."
                #  )
            else:
                self.chapter_content.setText(self.content)
                if not self.alt:
                    self.chapter_select.setCurrentIndex(APP.current_index)
        else:
            self.next_btn.setText("")
            self.next_btn.setEnabled(True)
            self.statusbar.showMessage("App Error: App not initialized properly.", 5000)
            msgBox(self, "App Error", "App not initialized properly.", error=True)
            #  QMessageBox.critical(self, "App Error", "App not initialized properly.")

    def on_stop(self) -> None:
        if APP is not None:
            APP.stop()
            play_icon = QPixmap("assets/icons/play.jpeg")
            self.toggle_play_btn.setIcon(QIcon(play_icon))
            self.statusbar.showMessage("Reading stopped...", 5000)
        else:
            self.statusbar.showMessage("App Error: App not initialized properly.", 5000)
            msgBox(self, "App Error", "App not initialized properly.", error=True)
            #  QMessageBox.critical(self, "App Error", "App not initialized properly.")

    @asyncSlot()
    async def togglePlayPause(self) -> None:
        if APP is not None:
            if APP.is_playing:
                APP.pause()
                pause_icon = QPixmap("assets/icons/pause.jpeg")
                self.toggle_play_btn.setIcon(QIcon(pause_icon))
                self.statusbar.showMessage("Reading paused...", 5000)
            else:
                if APP.player is not None:
                    APP.unpause()
                    play_icon = QPixmap("assets/icons/play.jpeg")
                    self.toggle_play_btn.setIcon(QIcon(play_icon))
                    self.statusbar.showMessage("Reading unpaused...", 5000)
                else:
                    await APP.read(self.content)
                    self.statusbar.showMessage("Reading started...", 5000)
        else:
            self.statusbar.showMessage("App Error: App not initialized properly.", 5000)
            msgBox(self, "App Error", "App not initialized properly.", error=True)
            #  QMessageBox.critical(self, "App Error", "App not initialized properly.")

    def setProgress(self) -> None:
        if APP is not None:
            self.progress_label.setText(APP.progress())
        else:
            self.statusbar.showMessage("App Error: App not initialized properly.", 5000)


class SlimeReader(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        loadUi("ui/SlimeReader.ui", self)

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

    @asyncSlot()
    async def on_ok(self) -> None:
        global LOCAL, ALT
        ALT = self.site_select.currentIndex()
        #  LOCAL = (
        #  False
        #  if (self.online.isChecked() and not self.offline.isChecked())
        #  else True
        #  )
        LOCAL = self.offline.isChecked()
        self.ok_btn.setText("Loading...")
        self.main = TensuraReader(LOCAL, bool(ALT))
        await self.main.init()
        self.ok_btn.setText("Done!")
        self.close()
        self.main.show()


def msgBox(root, title: str, content: str, error: bool = False) -> None:
    qmsgBox = QMessageBox(root)
    qmsgBox.setStyleSheet(
        "QMessageBox{background-color: rgb(20, 20, 20);color: rgb(20, 255, 255);}\n QPushButton{border-radius: 4px;padding: 6px;background-color: rgba(244, 164, 173, 200);color: rgb(20, 20, 20);}\n QPushButton:hover{background-color: rgb(244, 164, 173);}"
    )
    qmsgBox.setIcon(QMessageBox.Critical)
    qmsgBox.setWindowTitle(title)
    qmsgBox.setText(content)
    if error:
        qmsgBox.setStandardButtons(QMessageBox.Retry | QMessageBox.Ok)
        retval = qmsgBox.exec_()
        if retval == QMessageBox.Retry:
            restart()
    else:
        qmsgBox.setStandardButtons(QMessageBox.Ok)
        retval = qmsgBox.exec_()


def restart() -> None:
    """
    Restarts the Application

    NOTE: Buggy at the moment
    """
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
    #  app = QApplication(sys.argv)
    #  window = SlimeReader()
    #  window.show()
    #  sys.exit(app.exec())
    try:
        qasync.run(main())
    except asyncio.exceptions.CancelledError:
        sys.exit(0)
