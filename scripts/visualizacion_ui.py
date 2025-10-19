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
        Form.resize(1330, 570)
        self.nubesListWidget = QtWidgets.QListWidget(Form)
        self.nubesListWidget.setGeometry(QtCore.QRect(10, 80, 251, 481))
        self.nubesListWidget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.nubesListWidget.setObjectName("nubesListWidget")
        self.verNubePushButton = QtWidgets.QPushButton(Form)
        self.verNubePushButton.setGeometry(QtCore.QRect(210, 20, 51, 51))
        self.verNubePushButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/newPrefix/icons8-eye-90.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.verNubePushButton.setIcon(icon)
        self.verNubePushButton.setIconSize(QtCore.QSize(32, 32))
        self.verNubePushButton.setObjectName("verNubePushButton")
        self.generarReportePushButton = QtWidgets.QPushButton(Form)
        self.generarReportePushButton.setGeometry(QtCore.QRect(1160, 20, 151, 25))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/newPrefix/icons8-menu-60.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.generarReportePushButton.setIcon(icon1)
        self.generarReportePushButton.setObjectName("generarReportePushButton")
        self.vtkWidget = QtWidgets.QWidget(Form)
        self.vtkWidget.setGeometry(QtCore.QRect(280, 30, 771, 521))
        self.vtkWidget.setCursor(QtGui.QCursor(QtCore.Qt.SizeAllCursor))
        self.vtkWidget.setObjectName("vtkWidget")
        self.label_5 = QtWidgets.QLabel(Form)
        self.label_5.setGeometry(QtCore.QRect(1070, 350, 131, 17))
        self.label_5.setObjectName("label_5")
        self.descripcionNubeTextEdit = QtWidgets.QTextEdit(Form)
        self.descripcionNubeTextEdit.setGeometry(QtCore.QRect(1070, 380, 231, 111))
        self.descripcionNubeTextEdit.setObjectName("descripcionNubeTextEdit")
        self.label_6 = QtWidgets.QLabel(Form)
        self.label_6.setGeometry(QtCore.QRect(1070, 500, 67, 17))
        self.label_6.setObjectName("label_6")
        self.fechaLineEdit = QtWidgets.QLineEdit(Form)
        self.fechaLineEdit.setGeometry(QtCore.QRect(1070, 530, 231, 25))
        self.fechaLineEdit.setObjectName("fechaLineEdit")
        self.frame = QtWidgets.QFrame(Form)
        self.frame.setGeometry(QtCore.QRect(270, 20, 791, 541))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.label_10 = QtWidgets.QLabel(Form)
        self.label_10.setGeometry(QtCore.QRect(20, 50, 111, 21))
        font = QtGui.QFont()
        font.setFamily("Yrsa")
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.label_10.setFont(font)
        self.label_10.setObjectName("label_10")
        self.label_4 = QtWidgets.QLabel(Form)
        self.label_4.setGeometry(QtCore.QRect(20, 30, 91, 21))
        font = QtGui.QFont()
        font.setFamily("Yrsa")
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.frame.raise_()
        self.vtkWidget.raise_()
        self.nubesListWidget.raise_()
        self.verNubePushButton.raise_()
        self.generarReportePushButton.raise_()
        self.label_5.raise_()
        self.descripcionNubeTextEdit.raise_()
        self.label_6.raise_()
        self.fechaLineEdit.raise_()
        self.label_10.raise_()
        self.label_4.raise_()

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.verNubePushButton.setToolTip(_translate("Form", "Visualizar nube seleccionada"))
        self.generarReportePushButton.setText(_translate("Form", "Exportar PDF"))
        self.label_5.setText(_translate("Form", "Descripcion nube:"))
        self.label_6.setText(_translate("Form", "Fecha:"))
        self.label_10.setText(_translate("Form", "disponibes:"))
        self.label_4.setText(_translate("Form", "Nubes"))
import iconos_rc
