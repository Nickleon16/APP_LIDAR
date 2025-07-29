# main_window_node.py

from PyQt5.QtWidgets import QMainWindow
from main_window_ui import Ui_MainWindow
from user_registration_node import UserRegistrationWidget
from parametros_node import ParametrosWidget 
from procesamiento_node import ProcesamientoWidget
from visualizacion_node import VisualizacionWidget
from telecomando_node import TelecomandoWidget
import requests

class MainWindow(QMainWindow):
    def __init__(self, user_id):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Obtener nubes una sola vez
        self.nubes_cargadas = self.obtener_nubes_desde_backend()

        # --- Pestaña de usuarios ---
        self.user_widget = UserRegistrationWidget()
        self.user_widget.load_users()
        self.ui.tabWidget.addTab(self.user_widget, "Gestor usuarios")

        # --- Pestaña de parámetros ---
        self.parametros_widget = ParametrosWidget(user_id)
        self.ui.tabWidget.addTab(self.parametros_widget, "Parámetros")

        # --- Pestaña de procesamiento ---
        self.procesamiento_widget = ProcesamientoWidget(user_id, self.nubes_cargadas, self.actualizar_nubes_global)
        self.ui.tabWidget.addTab(self.procesamiento_widget, "Procesamiento")

        # --- Pestaña de visualizacion ---
        self.visualizacion_widget = VisualizacionWidget(user_id, self.nubes_cargadas)
        self.ui.tabWidget.addTab(self.visualizacion_widget, "Visualización")

        # --- Pestaña de telecomando ---
        self.telecomando_widget = TelecomandoWidget(user_id)
        self.ui.tabWidget.addTab(self.telecomando_widget, "Telecomando")

    #------------------------------------------------------------------------------

    def obtener_nubes_desde_backend(self):
        try:
            response = requests.get("http://127.0.0.1:5000/api/nube_puntos")
            if response.status_code == 200:
                return response.json().get("nubes", [])
        except Exception as e:
            print(f"[ERROR] Obteniendo nubes: {e}")
        return []

    #------------------------------------------------------------------------------

    def actualizar_nubes_global(self):
        self.nubes_cargadas = self.obtener_nubes_desde_backend()
        self.visualizacion_widget.actualizar_lista_externa(self.nubes_cargadas)
        self.procesamiento_widget.actualizar_lista_externa(self.nubes_cargadas)
