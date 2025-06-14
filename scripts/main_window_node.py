# main_window_node.py

from PyQt5.QtWidgets import QMainWindow
from main_window_ui import Ui_MainWindow
from user_registration_node import UserRegistrationWidget
from parametros_node import ParametrosWidget 
from procesamiento_node import ProcesamientoWidget

class MainWindow(QMainWindow):
    def __init__(self, user_id):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # --- Pestaña de usuarios ---
        self.user_widget = UserRegistrationWidget()
        self.user_widget.load_users()
        self.ui.tabWidget.addTab(self.user_widget, "Gestor usuarios")

        # --- Pestaña de parámetros ---
        self.parametros_widget = ParametrosWidget(user_id)
        self.ui.tabWidget.addTab(self.parametros_widget, "Parámetros")

        # --- Pestaña de procesamiento ---
        self.procesamiento_widget = ProcesamientoWidget(user_id)
        self.ui.tabWidget.addTab(self.procesamiento_widget, "Procesamiento")