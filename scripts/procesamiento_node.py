# procesamiento_node.py

import sys
from PyQt5.QtWidgets import QWidget, QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt
from procesamiento_ui import Ui_Form
import requests
from PyQt5.QtWidgets import QFileDialog
import tempfile
import open3d as o3d


class ProcesamientoWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.subirNubePushButton.clicked.connect(self.subir_nube_puntos)
        self.ui.verNubePushButton.clicked.connect(self.visualizar_nube)
        self.cargar_lista_nubes()


    def subir_nube_puntos(self):
        archivo_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de nube de puntos", "", "Nube de puntos (*.pcd *.ply *.xyz *.txt)")

        if archivo_path:
            try:
                with open(archivo_path, 'rb') as f:
                    datos = f.read()

                nombre = self.ui.nombreNubeLineEdit.text() or archivo_path.split("/")[-1]
                descripcion = self.ui.descripcionNubeLineEdit.text()

                files = {
                    'archivo': (nombre, datos)
                }
                data = {
                    'nombre': nombre,
                    'descripcion': descripcion
                }

                response = requests.post("http://127.0.0.1:5000/api/nube_puntos", files=files, data=data)

                if response.status_code == 201:
                    QMessageBox.information(self, "Éxito", "Archivo subido correctamente.")
                else:
                    QMessageBox.warning(self, "Error", response.text)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo subir el archivo: {str(e)}")
    
    def cargar_lista_nubes(self):
        try:
            response = requests.get("http://127.0.0.1:5000/api/nube_puntos")
            if response.status_code == 200:
                nubes = response.json().get("nubes", [])
                self.ui.nubesListWidget.clear()
                for n in nubes:
                    item = QListWidgetItem(f"{n['nubeID']} - {n['nombre']}")
                    item.setData(Qt.UserRole, n['nubeID'])
                    self.ui.nubesListWidget.addItem(item)
            else:
                QMessageBox.warning(self, "Error", "No se pudieron cargar las nubes.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")


    def visualizar_nube(self):
        item = self.ui.nubesListWidget.currentItem()
        if not item:
            QMessageBox.warning(self, "Atención", "Selecciona una nube para visualizar.")
            return

        nube_id = item.data(Qt.UserRole)

        try:
            response = requests.get(f"http://127.0.0.1:5000/api/nube_puntos/{nube_id}")
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pcd") as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name

                nube = o3d.io.read_point_cloud(tmp_path)
                o3d.visualization.draw_geometries([nube])
            else:
                QMessageBox.warning(self, "Error", "No se pudo descargar la nube.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al visualizar: {str(e)}")
