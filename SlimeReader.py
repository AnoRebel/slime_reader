import sys

try:
    from PyQt5 import QtGui, QtWidgets, QtCore, uic
except ImportError:
    from PySide2 import QtGui, QtWidgets, QtCore

from Tensura import Tensura

URL = 1
ALT = True


class TensuraReader(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("TensuraReader.ui", self)
        #  self.reader = await Tensura()
        self.connectSignals()
        self.statusbar.showMessage("Launched.", 2000)

    def connectSignals(self) -> None:
        self.action_Restart.triggered.connect(restart)
        self.action_Quit.triggered.connect(self.close)
        self.action_LoadLink.triggered.connect(self.loadLink)
        #  self.action_About.triggered.connect()

    def loadLink(self) -> None:
        dlg = ChapterLink()
        dlg.show()


class ChapterLink(QtWidgets.QDialog):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("ChapterLink.ui", self)
        self.cancel_dialog_btn.clicked.connect(self.close)
        #  self.load_chapter_btn.clicked.connect()


class SlimeReader(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("SlimeReader.ui", self)

        # Fix Bg Image
        self.frame.setStyleSheet(
            "QFrame {\n"
            "    border-radius: 6px;\n"
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
        self.exit_btn.clicked.connect(exit)
        self.ok_btn.clicked.connect(self.on_ok)

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
