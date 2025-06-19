# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI/visualizacion.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(860, 467)
        self.label_4 = QtWidgets.QLabel(Form)
        self.label_4.setGeometry(QtCore.QRect(10, 30, 131, 17))
        self.label_4.setObjectName("label_4")
        self.nubesListWidget = QtWidgets.QListWidget(Form)
        self.nubesListWidget.setGeometry(QtCore.QRect(10, 60, 251, 381))
        self.nubesListWidget.setObjectName("nubesListWidget")
        self.nombreNubeLineEdit = QtWidgets.QLineEdit(Form)
        self.nombreNubeLineEdit.setGeometry(QtCore.QRect(430, 70, 113, 25))
        self.nombreNubeLineEdit.setObjectName("nombreNubeLineEdit")
        self.descripcionNubeLineEdit = QtWidgets.QLineEdit(Form)
        self.descripcionNubeLineEdit.setGeometry(QtCore.QRect(430, 110, 113, 25))
        self.descripcionNubeLineEdit.setObjectName("descripcionNubeLineEdit")
        self.borrarNubePushButton = QtWidgets.QPushButton(Form)
        self.borrarNubePushButton.setGeometry(QtCore.QRect(300, 160, 101, 25))
        self.borrarNubePushButton.setObjectName("borrarNubePushButton")
        self.label_3 = QtWidgets.QLabel(Form)
        self.label_3.setGeometry(QtCore.QRect(300, 30, 171, 17))
        self.label_3.setObjectName("label_3")
        self.subirNubePushButton = QtWidgets.QPushButton(Form)
        self.subirNubePushButton.setGeometry(QtCore.QRect(450, 160, 89, 25))
        self.subirNubePushButton.setObjectName("subirNubePushButton")
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(300, 70, 101, 17))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setGeometry(QtCore.QRect(300, 110, 131, 17))
        self.label_2.setObjectName("label_2")
        self.verNubePushButton = QtWidgets.QPushButton(Form)
        self.verNubePushButton.setGeometry(QtCore.QRect(310, 210, 131, 25))
        self.verNubePushButton.setObjectName("verNubePushButton")
        self.generarReportePushButton = QtWidgets.QPushButton(Form)
        self.generarReportePushButton.setGeometry(QtCore.QRect(310, 420, 131, 25))
        self.generarReportePushButton.setObjectName("generarReportePushButton")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_4.setText(_translate("Form", "Nubes disponibes:"))
        self.borrarNubePushButton.setText(_translate("Form", "Borrar nube"))
        self.label_3.setText(_translate("Form", "Subir nubes de puntos:"))
        self.subirNubePushButton.setText(_translate("Form", "Subir nube"))
        self.label.setText(_translate("Form", "Nombre nube:"))
        self.label_2.setText(_translate("Form", "Descripcion nube:"))
        self.verNubePushButton.setText(_translate("Form", "Visualizar nube"))
        self.generarReportePushButton.setText(_translate("Form", "Exportar PDF"))
