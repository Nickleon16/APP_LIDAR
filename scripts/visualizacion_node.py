# visualizacion_node.py

import os
import numpy as np
import open3d as o3d
import requests

from PyQt5.QtWidgets import QWidget, QMessageBox, QListWidgetItem, QFileDialog, QVBoxLayout
from PyQt5.QtCore import Qt

from visualizacion_ui import Ui_Form

import pyvista as pv
from pyvistaqt import QtInteractor

import tempfile

from fpdf import FPDF

class VisualizacionWidget(QWidget):
    def __init__(self, user_id, lista_nubes):
        super().__init__()
        self.user_id = user_id
        self.lista_nubes = lista_nubes
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Embebemos PyVista en el QWidget definido en Qt Designer
        self.pv_layout = QVBoxLayout(self.ui.vtkWidget)
        self.plotter = QtInteractor(self.ui.vtkWidget)
        self.pv_layout.addWidget(self.plotter)

        # Conectar botones
        self.ui.subirNubePushButton.clicked.connect(self.subir_nube_puntos)
        self.ui.verNubePushButton.clicked.connect(self.visualizar_nube)
        self.ui.borrarNubePushButton.clicked.connect(self.eliminar_nube)
        self.ui.generarReportePushButton.clicked.connect(self.generar_reporte_pdf)

        self.actualizar_lista_externa(self.lista_nubes)

#-----------------------------------------------------------------------------

    def actualizar_lista_externa(self, nueva_lista):
        self.lista_nubes = nueva_lista
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
        self.ui.nubesListWidget.clear()
        for n in self.lista_nubes:
            item = QListWidgetItem(f"{n['nubeID']} - {n['nombre']}")
            item.setData(Qt.UserRole, n["nubeID"])
            self.ui.nubesListWidget.addItem(item)

#-----------------------------------------------------------------------------

    def visualizar_nube(self):
        try:
            # Obtener ítem seleccionado
            item = self.ui.nubesListWidget.currentItem()
            if not item:
                QMessageBox.warning(self, "Advertencia", "Selecciona una nube primero.")
                return

            nube_id = item.data(Qt.UserRole)

            # Obtener metadatos
            meta_response = requests.get(f"http://127.0.0.1:5000/api/nube_puntos/{nube_id}/info")
            if meta_response.status_code != 200:
                QMessageBox.critical(self, "Error", "No se pudo obtener la información de la nube.")
                return

            meta = meta_response.json()
            nombre = meta["nombre"]
            extension = meta["archivo_tipo"]
            descripcion = meta.get("descripcion", "")
            fecha = meta.get("fecha", "Desconocida")

            # Mostrar descripción y nombre en los campos
            self.ui.descripcionNubeTextEdit.setPlainText(descripcion)
            self.ui.fechaLineEdit.setText(fecha)


            # Descargar archivo
            response = requests.get(f"http://127.0.0.1:5000/api/nube_puntos/{nube_id}")
            if response.status_code != 200:
                QMessageBox.critical(self, "Error", f"Error al visualizar: {response.text}")
                return

            # Guardar temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name

            # Leer y convertir con Open3D
            pcd = o3d.io.read_point_cloud(tmp_path)
            puntos = np.asarray(pcd.points)
            os.remove(tmp_path)

            if puntos.size == 0:
                QMessageBox.warning(self, "Advertencia", f"La nube '{nombre}' está vacía.")
                return

            # Crear visualización con PyVista
            cloud = pv.PolyData(puntos)
            z = puntos[:, 2]
            z -= z.min()  # Asegurar que no haya valores negativos
            cloud["altura"] = z

            self.plotter.clear()
            self.plotter.add_mesh(
                cloud,
                scalars="altura",
                cmap="viridis",
                point_size=3,
                render_points_as_spheres=True,
                scalar_bar_args={
                    "title": "Profundidad (m)",
                    "vertical": True,
                    "title_font_size": 12,
                    "label_font_size": 10
                }
            )
            self.plotter.reset_camera()
            self.plotter.render()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al visualizar la nube: {str(e)}")

#-----------------------------------------------------------------------------

    def generar_reporte_pdf(self):
        item = self.ui.nubesListWidget.currentItem()
        if not item:
            QMessageBox.warning(self, "Atención", "Selecciona una nube para generar el reporte.")
            return

        nube_id = item.data(Qt.UserRole)

        try:
            # 1. Descargar nube desde la API
            response = requests.get(f"http://127.0.0.1:5000/api/nube_puntos/{nube_id}")
            if response.status_code != 200:
                QMessageBox.warning(self, "Error", "No se pudo descargar la nube.")
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pcd") as tmp_pcd:
                tmp_pcd.write(response.content)
                path_pcd = tmp_pcd.name

            # 2. Renderizar imagen
            path_img = path_pcd.replace(".pcd", ".png")
            renderizar_nube_a_imagen(path_pcd, path_img)

            # 3. Convertir a LAS
            path_las = path_pcd.replace(".pcd", ".las")
            convertir_a_las(path_pcd, path_las)

            # 4. Crear PDF
            
            def obtener_datos_usuario(user_id):
                try:
                    response = requests.get(f"http://127.0.0.1:5000/api/usuarios/{user_id}")
                    if response.status_code == 200:
                        return response.json()
                    else:
                        print("Error al obtener datos del usuario:", response.text)
                        return {}
                except Exception as e:
                    print("Excepción:", e)
                    return {}

            usuario = obtener_datos_usuario(self.user_id)
            parametros = {"Resolución": "0.05 m", "Filtro": "Voxel", "Método": "None"}
            
            pdf = ReportePDF()
            pdf.add_page()
            pdf.agregar_info_usuario(usuario)
            pdf.add_parametros(parametros)
            pdf.add_nube_3d_img(path_img)
            pdf.add_las_info(path_las)

            save_path, _ = QFileDialog.getSaveFileName(self, "Guardar reporte", "", "PDF (*.pdf)")
            if save_path:
                pdf.output(save_path)
                QMessageBox.information(self, "Éxito", "Reporte generado correctamente.")
            else:
                QMessageBox.information(self, "Cancelado", "No se guardó el reporte.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar el reporte: {str(e)}")



#-----------------------------------------------------------------------------

    def eliminar_nube(self):
        item = self.ui.nubesListWidget.currentItem()
        if not item:
            QMessageBox.warning(self, "Atención", "Selecciona una nube para eliminar.")
            return

        nube_id = item.data(Qt.UserRole)

        confirm = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar la nube ID {nube_id}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            try:
                response = requests.delete(f"http://127.0.0.1:5000/api/nube_puntos/{nube_id}")
                if response.status_code == 200:
                    QMessageBox.information(self, "Eliminado", "Nube eliminada correctamente.")
                    self.cargar_lista_nubes()  # refresca la lista
                else:
                    QMessageBox.warning(self, "Error", f"No se pudo eliminar la nube: {response.text}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar: {str(e)}")

#-----------------------------------------------------------------------------


class ReportePDF(FPDF):
    def header(self):
        # Logos alineados a la derecha
        logo_width = 20
        espacio_entre_logos = 5
        margen_derecho = 10
        y_logo = 10                

        # Segundo logo (más a la derecha)
        x_logo2 = self.w - margen_derecho - logo_width
        self.image("recursos/Univalle.png", x=x_logo2, y=y_logo, w=logo_width)

        # Primer logo a la izquierda del segundo
        x_logo1 = x_logo2 - espacio_entre_logos - logo_width
        self.image("recursos/psi.png", x=x_logo1-45, y=y_logo, w=logo_width+45)

        # Título centrado debajo de los logos
        self.set_xy(0, y_logo + logo_width + 12)
        self.set_font("Arial", 'B', 14)
        self.cell(0, 10, "Reporte de Análisis LIDAR", ln=True, align="C")

        # Línea separadora
        self.set_line_width(0.5)
        self.line(10, self.get_y(), self.w - 10, self.get_y())

    def agregar_info_usuario(self, usuario):
        self.ln(8)
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "Información de usuario:", ln=True)
        self.set_font("Arial", "", 10)                
        self.cell(0, 10, f"Nombre: {usuario.get('nombre', 'N/A')}", ln=True)
        self.cell(0, 10, f"Email: {usuario.get('email', 'N/A')}", ln=True)
        self.cell(0, 10, f"Rol: {usuario.get('rol', 'N/A')}", ln=True)

    def add_parametros(self, params):
        self.ln(5)
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "Parámetros:", ln=True)
        self.set_font("Arial", size=11)
        for k, v in params.items():
            self.cell(0, 8, f"{k}: {v}", ln=True)

    def add_nube_3d_img(self, img_path):
        self.ln(5)
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "Visualización 3D:", ln=True)
        self.image(img_path, x=15, w=180)

    def add_las_info(self, las_path):
        self.set_font("Arial", size=12)
        self.ln(10)
        self.cell(0, 10, f"Nube en formato LAS: {os.path.basename(las_path)}", ln=True)
#--------------------------------------------------------------------

def renderizar_nube_a_imagen(pcd_path, out_path_img):
    nube = o3d.io.read_point_cloud(pcd_path)
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False)
    vis.add_geometry(nube)
    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(out_path_img)
    vis.destroy_window()

def convertir_a_las(pcd_path, out_path_las):
    nube = o3d.io.read_point_cloud(pcd_path)
    puntos = np.asarray(nube.points)

    header = laspy.LasHeader(point_format=3, version="1.2")
    las = laspy.LasData(header)
    las.x = puntos[:, 0]
    las.y = puntos[:, 1]
    las.z = puntos[:, 2]
    las.write(out_path_las)
