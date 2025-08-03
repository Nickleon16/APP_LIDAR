# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI/main_window.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1360, 700)
        self.tabWidget = QtWidgets.QTabWidget(MainWindow)
        self.tabWidget.setGeometry(QtCore.QRect(10, 0, 1340, 611))
        self.tabWidget.setObjectName("tabWidget")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.label = QtWidgets.QLabel(MainWindow)
        self.label.setGeometry(QtCore.QRect(1080, 620, 201, 71))
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(":/iconos/iconos/psi.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(MainWindow)
        self.label_2.setGeometry(QtCore.QRect(1300, 620, 51, 71))
        self.label_2.setText("")
        self.label_2.setPixmap(QtGui.QPixmap(":/iconos/iconos/univalle.png"))
        self.label_2.setScaledContents(True)
        self.label_2.setObjectName("label_2")

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Captura"))
import iconos_rc
