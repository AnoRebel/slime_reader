# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/AboutDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        AboutDialog.setObjectName("AboutDialog")
        AboutDialog.resize(400, 200)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AboutDialog.sizePolicy().hasHeightForWidth())
        AboutDialog.setSizePolicy(sizePolicy)
        AboutDialog.setMinimumSize(QtCore.QSize(400, 200))
        AboutDialog.setMaximumSize(QtCore.QSize(400, 200))
        AboutDialog.setBaseSize(QtCore.QSize(400, 200))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/assets/icons/bg-icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        AboutDialog.setWindowIcon(icon)
        AboutDialog.setStyleSheet("border-radius: 6px;\n"
"background-color: rgb(20, 20, 20);")
        self.verticalLayout = QtWidgets.QVBoxLayout(AboutDialog)
        self.verticalLayout.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(AboutDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMinimumSize(QtCore.QSize(392, 192))
        self.frame.setMaximumSize(QtCore.QSize(392, 192))
        self.frame.setBaseSize(QtCore.QSize(392, 192))
        self.frame.setStyleSheet("QFrame{\n"
"    color: #ECECEC;\n"
"    border-radius: 6px;\n"
"    background-color: rgb(20, 20, 20);\n"
"}")
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.app_image = QtWidgets.QLabel(self.frame)
        self.app_image.setGeometry(QtCore.QRect(250, 10, 121, 121))
        self.app_image.setStyleSheet("border-radius: 6px;")
        self.app_image.setText("")
        self.app_image.setPixmap(QtGui.QPixmap(":/images/assets/images/rimuru.jpeg"))
        self.app_image.setScaledContents(True)
        self.app_image.setAlignment(QtCore.Qt.AlignCenter)
        self.app_image.setObjectName("app_image")
        self.dismiss_btn = QtWidgets.QPushButton(self.frame)
        self.dismiss_btn.setGeometry(QtCore.QRect(280, 150, 91, 31))
        font = QtGui.QFont()
        font.setFamily("DroidSansMono NF")
        font.setPointSize(12)
        self.dismiss_btn.setFont(font)
        self.dismiss_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.dismiss_btn.setStyleSheet("QPushButton{\n"
"    background-color: rgba(85, 255, 255, 160);\n"
"    border-radius: 4px;\n"
"    color: #141414;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: rgba(85, 255, 255, 190);\n"
"}")
        self.dismiss_btn.setIcon(icon)
        self.dismiss_btn.setObjectName("dismiss_btn")
        self.app_name = QtWidgets.QLabel(self.frame)
        self.app_name.setGeometry(QtCore.QRect(20, 10, 161, 41))
        font = QtGui.QFont()
        font.setFamily("Lato Heavy")
        font.setPointSize(16)
        font.setBold(False)
        font.setWeight(50)
        self.app_name.setFont(font)
        self.app_name.setStyleSheet("color: rgb(85, 255, 255);")
        self.app_name.setObjectName("app_name")
        self.app_description = QtWidgets.QLabel(self.frame)
        self.app_description.setGeometry(QtCore.QRect(20, 60, 221, 71))
        font = QtGui.QFont()
        font.setFamily("DroidSansMono NF")
        self.app_description.setFont(font)
        self.app_description.setStyleSheet("QLabel:hover {\n"
"    color: rgb(85, 255, 255);\n"
"}")
        self.app_description.setWordWrap(True)
        self.app_description.setObjectName("app_description")
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi(AboutDialog)
        QtCore.QMetaObject.connectSlotsByName(AboutDialog)

    def retranslateUi(self, AboutDialog):
        _translate = QtCore.QCoreApplication.translate
        AboutDialog.setWindowTitle(_translate("AboutDialog", "Tensura Reader - About"))
        self.dismiss_btn.setText(_translate("AboutDialog", "Ok"))
        self.app_name.setText(_translate("AboutDialog", "Tensura Reader"))
        self.app_description.setText(_translate("AboutDialog", "A simple GUI for the Tensura script I created to scrape and read for me Tensura(since I\'m too lazy)"))
import tensura_rc
