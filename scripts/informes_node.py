# informes_node.py

from PyQt5.QtWidgets import QWidget, QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt
from informes_ui import Ui_Form

class InformesWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.ui = Ui_Form()
        self.ui.setupUi(self)        

        # Conectar botones        
        self.ui.generarReportePushButton.clicked.connect(self.generar_reporte_pdf)
