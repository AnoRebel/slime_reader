import sys

# if "PyQt5" in sys.modules:
#    # PyQt5
from PyQt5 import QtGui, QtWidgets, QtCore, uic
from PyQt5.QtCore import pyqtSignal as Signal, pyqtSlot as Slot

# else:
#    # PySide2
#    from PySide2 import QtGui, QtWidgets, QtCore
#    from PySide2.QtCore import Signal, Slot

# from Tensura import Tensura
URL = 1
ALT = True


class TensuraReader(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("TensuraReader.ui", self)


class SlimeReader(QtWidgets.QMainWindow):
    def __init__(self):
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

    def on_ok(self):
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = SlimeReader()
    window.show()
    sys.exit(app.exec())
