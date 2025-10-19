# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI/login.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_loginWindow(object):
    def setupUi(self, loginWindow):
        loginWindow.setObjectName("loginWindow")
        loginWindow.resize(400, 300)
        self.label = QtWidgets.QLabel(loginWindow)
        self.label.setGeometry(QtCore.QRect(90, 50, 67, 17))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(loginWindow)
        self.label_2.setGeometry(QtCore.QRect(90, 90, 101, 17))
        self.label_2.setObjectName("label_2")
        self.usernameLineEdit = QtWidgets.QLineEdit(loginWindow)
        self.usernameLineEdit.setGeometry(QtCore.QRect(190, 50, 113, 25))
        self.usernameLineEdit.setObjectName("usernameLineEdit")
        self.passwordLineEdit = QtWidgets.QLineEdit(loginWindow)
        self.passwordLineEdit.setGeometry(QtCore.QRect(190, 90, 113, 25))
        self.passwordLineEdit.setObjectName("passwordLineEdit")
        self.confirmButton = QtWidgets.QPushButton(loginWindow)
        self.confirmButton.setGeometry(QtCore.QRect(198, 150, 101, 25))
        self.confirmButton.setObjectName("confirmButton")
        self.clearButton = QtWidgets.QPushButton(loginWindow)
        self.clearButton.setGeometry(QtCore.QRect(90, 150, 89, 25))
        self.clearButton.setObjectName("clearButton")
        self.label_3 = QtWidgets.QLabel(loginWindow)
        self.label_3.setGeometry(QtCore.QRect(270, 200, 61, 81))
        self.label_3.setText("")
        self.label_3.setPixmap(QtGui.QPixmap(":/newPrefix/univalle.png"))
        self.label_3.setScaledContents(True)
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(loginWindow)
        self.label_4.setGeometry(QtCore.QRect(60, 200, 201, 81))
        self.label_4.setText("")
        self.label_4.setPixmap(QtGui.QPixmap(":/newPrefix/psi.png"))
        self.label_4.setScaledContents(True)
        self.label_4.setObjectName("label_4")

        self.retranslateUi(loginWindow)
        QtCore.QMetaObject.connectSlotsByName(loginWindow)

    def retranslateUi(self, loginWindow):
        _translate = QtCore.QCoreApplication.translate
        loginWindow.setWindowTitle(_translate("loginWindow", "loginWindow"))
        self.label.setText(_translate("loginWindow", "Usuario:"))
        self.label_2.setText(_translate("loginWindow", "Contraseña:"))
        self.confirmButton.setText(_translate("loginWindow", "Confirmar"))
        self.clearButton.setText(_translate("loginWindow", "Limpiar"))
import iconos_rc
