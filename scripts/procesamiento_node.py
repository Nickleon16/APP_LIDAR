# procesamiento_node.py

import os
import tempfile
import re

from PyQt5.QtWidgets import QWidget, QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt
from procesamiento_ui import Ui_Form
import requests
from PyQt5.QtWidgets import QFileDialog
import tempfile
import open3d as o3d
import subprocess
import tempfile


class ProcesamientoWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.subirNubePushButton.clicked.connect(self.subir_nube_puntos)
        self.ui.verNubePushButton.clicked.connect(self.visualizar_nube)
        self.cargar_lista_nubes()

#-----------------------------------------------------------------------------

    def subir_nube_puntos(self):
        archivo_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de nube de puntos", "", "Nube de puntos (*.pcd *.ply *.xyz *.txt)")

        if archivo_path:
            try:
                with open(archivo_path, 'rb') as f:
                    datos = f.read()

                # Asegúrate de usar el nombre con extensión real
                nombre_archivo = os.path.basename(archivo_path)
                extension = os.path.splitext(nombre_archivo)[-1].lstrip('.')  # 'pcd', 'ply', etc.

                nombre = self.ui.nombreNubeLineEdit.text() or os.path.splitext(nombre_archivo)[0]
                descripcion = self.ui.descripcionNubeLineEdit.text()

                files = {
                    'archivo': (nombre_archivo, datos)
                }
                data = {
                    'nombre': nombre,
                    'descripcion': descripcion,
                    'nombre_archivo': nombre_archivo
                }

                response = requests.post("http://127.0.0.1:5000/api/nube_puntos", files=files, data=data)
                if response.status_code == 201:                    
                    QMessageBox.information(self, "Éxito", "Archivo subido correctamente.")
                    self.cargar_lista_nubes()
                else:
                    QMessageBox.warning(self, "Error", response.text)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo subir el archivo: {str(e)}")
    
#-----------------------------------------------------------------------------

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

#-----------------------------------------------------------------------------
    
    def visualizar_nube(self, nube_id):
        
        nube_id = self.ui.nubesListWidget.currentItem().data(Qt.UserRole)
        try:
            response = requests.get(f"http://127.0.0.1:5000/api/nube_puntos/{nube_id}")
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pcd") as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name

                # Llama a otro script que visualiza sin Qt ni ROS
                subprocess.Popen(["python3", "visualizador_nubes.py", tmp_path])
            else:
                QMessageBox.warning(self, "Error", "No se pudo descargar la nube.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al visualizar: {str(e)}")