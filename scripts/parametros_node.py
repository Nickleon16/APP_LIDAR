import sys
from PyQt5.QtWidgets import QWidget, QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt
from parametros_ui import Ui_Form
import requests

class ParametrosWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.parametro_id = None

        # Conectar botones        
        self.ui.confirmarPushButton.clicked.connect(self.save_parametros)
        self.ui.loadDefaultsButton.clicked.connect(self.cargar_parametros_por_defecto)
        self.ui.presetsListWidget.itemClicked.connect(self.seleccionar_preset)
        self.ui.nuevoPresetButton.clicked.connect(self.nuevo_preset)
        self.ui.eliminarPresetpushButton.clicked.connect(self.eliminar_preset)

        # Cargamos la lista de presets (parametros)
        self.load_parametros()

#----------------------------------------------------------------------------------

    def save_parametros(self):
        data = {
            "usuario_id": self.user_id,
            "nombre_preset": self.ui.nombrePresetLineEdit.text(),
            "descripcion": self.ui.descripcionLineEdit.text(),

            "velocidad_maxima": self.ui.velMaxSpinBox.value(),
            "velocidad_lineal": self.ui.velLineSpinBox.value(),
            "velocidad_angular": self.ui.velAnguSpinBox.value(),

            "tasa_muestreo": None,
            "campo_vision": None,
            "resolucion": None,
            "filtro_ruido": None,
            "metodo_filtrado": None,
            "reduccion_ruido": None,
            "compensacion_movimiento": None,
            "metodo_procesamiento": None,
            "tolerancia": None,
            "iteraciones": None,
            "correspondencia": None
        }

        try:
            if self.parametro_id:
                url = f"http://127.0.0.1:5000/api/parametros/{self.parametro_id}"
                response = requests.put(url, json=data)
            else:
                url = "http://127.0.0.1:5000/api/parametros"
                response = requests.post(url, json=data)

            if response.status_code in [200, 201]:
                QMessageBox.information(self, "Éxito", "Preset guardado.")
                self.load_parametros()  # Recargar la lista de presets
                # self.limpiar_formulario() (opcional)
            else:
                QMessageBox.warning(self, "Error", response.text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")

#----------------------------------------------------------------------------------

    def load_parametros(self):
        """Carga la lista de presets (parametros) para el usuario"""
        try:
            response = requests.get(f"http://127.0.0.1:5000/api/parametros/por_usuario/{self.user_id}")
            if response.status_code == 200:
                parametros_list = response.json().get("parametros", [])  # <<< aquí ya usamos "parametros"

                self.ui.presetsListWidget.clear()

                for p in parametros_list:
                    item_text = f"{p['nombre_preset']} (ID {p['parametroID']})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, p['parametroID'])
                    self.ui.presetsListWidget.addItem(item)
            else:
                QMessageBox.warning(self, "Error", "No se pudieron cargar los presets.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")

#----------------------------------------------------------------------------------

    def cargar_parametros_por_defecto(self):
        try:
            response = requests.get("http://127.0.0.1:5000/api/parametros/default")
            if response.status_code == 200:
                defaults = response.json().get("parametros", {})

                self.ui.nombrePresetLineEdit.setText(defaults.get("nombre_preset", "Default"))
                self.ui.descripcionLineEdit.setText(defaults.get("descripcion", ""))
                self.ui.velMaxSpinBox.setValue(defaults.get("velocidad_maxima", 0.0))
                self.ui.velLineSpinBox.setValue(defaults.get("velocidad_lineal", 0.0))
                self.ui.velAnguSpinBox.setValue(defaults.get("velocidad_angular", 0.0))

                QMessageBox.information(self, "Info", "Parámetros por defecto cargados.")
            else:
                QMessageBox.warning(self, "Error", "No se pudieron cargar los parámetros por defecto.")
                self.ui.descripcionLineEdit.setText("Todo mal")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")

#----------------------------------------------------------------------------------

    def seleccionar_preset(self, item):
        """Cuando se selecciona un preset en la lista, cargarlo"""
        parametro_id = item.data(Qt.UserRole)
        self.parametro_id = parametro_id  # estamos en modo "editar"

        try:
            response = requests.get(f"http://127.0.0.1:5000/api/parametros/{parametro_id}")
            if response.status_code == 200:
                p = response.json().get("parametros", {})

                self.ui.nombrePresetLineEdit.setText(p.get("nombre_preset", ""))
                self.ui.descripcionLineEdit.setText(p.get("descripcion", ""))
                self.ui.velMaxSpinBox.setValue(p.get("velocidad_maxima", 0.0))
                self.ui.velLineSpinBox.setValue(p.get("velocidad_lineal", 0.0))
                self.ui.velAnguSpinBox.setValue(p.get("velocidad_angular", 0.0))
                # ... el resto de campos si los usas
            else:
                QMessageBox.warning(self, "Error", "No se pudo cargar el preset seleccionado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")

#----------------------------------------------------------------------------------

    def nuevo_preset(self):
        """Prepara el formulario para crear un nuevo preset"""
        self.parametro_id = None  # modo "crear nuevo"
        self.ui.nombrePresetLineEdit.clear()
        self.ui.descripcionLineEdit.clear()
        self.ui.velMaxSpinBox.setValue(0.0)
        self.ui.velLineSpinBox.setValue(0.0)
        self.ui.velAnguSpinBox.setValue(0.0)
        # ... limpiar el resto de campos

        self.ui.presetsListWidget.clearSelection()  # deseleccionar cualquier preset

#----------------------------------------------------------------------------------

    def eliminar_preset(self):
        if not self.parametro_id:
            QMessageBox.warning(self, "Aviso", "No hay preset seleccionado para eliminar.")
            return

        # Confirmación
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Está seguro de que desea eliminar este preset?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        try:
            response = requests.delete(f"http://127.0.0.1:5000/api/parametros/{self.parametro_id}")
            if response.status_code == 200:
                QMessageBox.information(self, "Éxito", "Preset eliminado.")
                self.nuevo_preset()   # limpiar formulario
                self.load_parametros()  # recargar lista
            else:
                QMessageBox.warning(self, "Error", response.text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")
