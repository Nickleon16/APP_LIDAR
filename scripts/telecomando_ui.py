# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI/telecomando.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(860, 459)
        self.avanzarPushButton = QtWidgets.QPushButton(Form)
        self.avanzarPushButton.setGeometry(QtCore.QRect(120, 100, 71, 25))
        self.avanzarPushButton.setObjectName("avanzarPushButton")
        self.reversaPushButton = QtWidgets.QPushButton(Form)
        self.reversaPushButton.setGeometry(QtCore.QRect(120, 180, 71, 25))
        self.reversaPushButton.setObjectName("reversaPushButton")
        self.izquierdaPushButton = QtWidgets.QPushButton(Form)
        self.izquierdaPushButton.setGeometry(QtCore.QRect(28, 140, 81, 25))
        self.izquierdaPushButton.setObjectName("izquierdaPushButton")
        self.derechaPushButton = QtWidgets.QPushButton(Form)
        self.derechaPushButton.setGeometry(QtCore.QRect(200, 140, 81, 25))
        self.derechaPushButton.setObjectName("derechaPushButton")
        self.stopPushButton = QtWidgets.QPushButton(Form)
        self.stopPushButton.setGeometry(QtCore.QRect(120, 140, 71, 25))
        self.stopPushButton.setObjectName("stopPushButton")
        self.posicionLabel = QtWidgets.QLabel(Form)
        self.posicionLabel.setGeometry(QtCore.QRect(320, 70, 241, 17))
        self.posicionLabel.setObjectName("posicionLabel")
        self.velocidadLabel = QtWidgets.QLabel(Form)
        self.velocidadLabel.setGeometry(QtCore.QRect(320, 110, 381, 17))
        self.velocidadLabel.setObjectName("velocidadLabel")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.avanzarPushButton.setText(_translate("Form", "Avanzar"))
        self.reversaPushButton.setText(_translate("Form", "Reversa"))
        self.izquierdaPushButton.setText(_translate("Form", "Girar Izq."))
        self.derechaPushButton.setText(_translate("Form", "Girar Der."))
        self.stopPushButton.setText(_translate("Form", "Stop"))
        self.posicionLabel.setText(_translate("Form", "Posición:"))
        self.velocidadLabel.setText(_translate("Form", "Velocidad:"))
