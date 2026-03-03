# visualizacion_node.py

import os
import numpy as np
import open3d as o3d
import requests
from PyQt5.QtWidgets import QInputDialog

from PyQt5.QtWidgets import QWidget, QMessageBox, QListWidgetItem, QFileDialog, QVBoxLayout
from PyQt5.QtCore import Qt

from visualizacion_ui import Ui_Form
from parametros_node import ParametrosWidget

import pyvista as pv
from pyvistaqt import QtInteractor

import tempfile

from fpdf import FPDF
import laspy
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D 

class VisualizacionWidget(QWidget):
    def __init__(self, user_id, lista_nubes, parametros_widget):

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
        self.ui.verNubePushButton.clicked.connect(self.visualizar_nube)        
        self.ui.generarReportePushButton.clicked.connect(self.generar_reporte_pdf)

        self.param_widget = parametros_widget

        self.actualizar_lista_externa(self.lista_nubes)

#-----------------------------------------------------------------------------

    def actualizar_lista_externa(self, nueva_lista):
        self.lista_nubes = nueva_lista
        self.cargar_lista_nubes()

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
            items = self.ui.nubesListWidget.selectedItems()
            if not items:
                QMessageBox.warning(self, "Advertencia", "Selecciona al menos una nube.")
                return
            if len(items) > 2:
                QMessageBox.warning(self, "Advertencia", "Selecciona como máximo dos nubes para comparar.")
                return

            geometrías = []
            etiquetas = []
            desplazamiento_total = 0.0

            colores_fallback = [[1, 0, 0], [0, 1, 0]]  # solo para etiquetas si no hay colores

            nubes_response = requests.get("http://127.0.0.1:5000/api/nube_puntos").json()["nubes"]

            for i, item in enumerate(items):
                nube_id = item.data(Qt.UserRole)
                nube_info = next((n for n in nubes_response if n["nubeID"] == nube_id), None)

                response = requests.get(f"http://127.0.0.1:5000/api/nube_puntos/{nube_id}")
                if response.status_code != 200:
                    QMessageBox.critical(self, "Error", f"No se pudo visualizar la nube {nube_id}")
                    return

                extension = nube_info["archivo_tipo"]
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name

                pcd = o3d.io.read_point_cloud(tmp_path)
                puntos = np.asarray(pcd.points)
                os.remove(tmp_path)

                if puntos.size == 0:
                    QMessageBox.warning(self, "Advertencia", f"La nube '{nube_info['nombre']}' está vacía.")
                    return

                # Bounding box para desplazamiento horizontal
                bbox = pcd.get_axis_aligned_bounding_box()
                ancho = bbox.get_extent()[0]

                if i == 1:
                    puntos = puntos + np.array([desplazamiento_total + ancho * 0.6, 0, 0])

                desplazamiento_total += ancho * 0.6

                cloud = pv.PolyData(puntos)

                # Visualización adaptativa: colores RGB o altura Z
                if len(pcd.colors) > 0:
                    colors = np.asarray(pcd.colors)
                    cloud["RGB"] = (colors * 255).astype(np.uint8)
                    geometrías.append(("rgb", cloud))
                else:
                    z = puntos[:, 2]
                    z -= z.min()
                    cloud["altura"] = z
                    geometrías.append(("altura", cloud))

                centro = np.mean(puntos, axis=0)
                etiquetas.append((centro, nube_info["nombre"]))

            # Mostrar descripción
            if len(items) == 1:
                self.ui.descripcionNubeTextEdit.setText(nube_info.get("descripcion", "Sin descripción."))
                self.ui.fechaLineEdit.setText(nube_info.get("fecha", "Fecha no disponible."))
            else:
                self.ui.descripcionNubeTextEdit.setText("Comparación entre dos nubes separadas espacialmente.")

            # Visualización final
            self.plotter.clear()

            for tipo, cloud in geometrías:
                if tipo == "rgb":
                    self.plotter.add_mesh(
                        cloud,
                        scalars="RGB",
                        rgb=True,
                        point_size=3,
                        render_points_as_spheres=True
                    )
                else:
                    self.plotter.add_mesh(
                        cloud,
                        scalars="altura",
                        cmap="viridis",
                        point_size=3,
                        render_points_as_spheres=True,
                        scalar_bar_args={
                            "title": "Profundidad (m)",
                            "vertical": True,
                            "title_font_size": 11,
                            "label_font_size": 9
                        }
                    )

            for pos, texto in etiquetas:
                self.plotter.add_point_labels([pos], [texto], font_size=12, point_size=0, text_color="white")

            self.plotter.reset_camera()
            self.plotter.render()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al visualizar la(s) nube(s): {str(e)}")

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
            renderizar_nube_con_matplotlib(path_pcd, path_img)

            # 3. Convertir a LAS
            path_las = path_pcd.replace(".pcd", ".las")
            convertir_a_las(path_pcd, path_las)

            # 4. Crear PDF
            
            def obtener_datos_usuario(user_id):
                try:
                    response = requests.get(f"http://127.0.0.1:5000/api/usuario/{user_id}")
                    if response.status_code == 200:
                        return response.json()
                    else:
                        print("Error al obtener datos del usuario:", response.text)
                        return {}
                except Exception as e:
                    print("Excepción:", e)
                    return {}
                
            def obtener_parametros(parametroID):
                try:
                    response = requests.get(f"http://127.0.0.1:5000/api/parametros/{parametroID}")
                    if response.status_code == 200:
                        parametros = response.json().get("parametros", {})
                        return parametros
                    else:
                        print("Error al obtener parámetros de la nube:", response.text)
                        return {}
                except Exception as e:
                    print("Excepción:", e)
                    return {}
            
            # Obtener info de la nube
            meta_resp = requests.get(f"http://127.0.0.1:5000/api/nube_puntos/{nube_id}/info")
            if meta_resp.status_code == 200:
                info_nube = meta_resp.json()
            else:
                info_nube = {
                    "nombre": "Desconocido",
                    "descripcion": "Sin descripción",
                    "parametroID": None
                }

            # Obtener parámetros seleccionados
            parametroID = self.param_widget.obtener_parametro_seleccionado()            

            usuario = obtener_datos_usuario(self.user_id)
            parametros = obtener_parametros(parametroID)
            
            pdf = ReportePDF()
            pdf.add_page()
            pdf.agregar_info_usuario(usuario)
            pdf.add_info_nube(
                info_nube.get("nombre", "Sin nombre"),
                info_nube.get("descripcion", "Sin descripción"),
                info_nube.get("fecha", "N/A")
            )
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

class ReportePDF(FPDF):    
    def header(self):
        margen_derecho = 10
        espacio = 8
        y_logo = 10

        # Tamaños reales
        w_univalle = 15
        w_psi = 55
        w_app = 90

        # Logo derecha (Univalle)
        x_univalle = self.w - margen_derecho - w_univalle
        self.image("recursos/univalle.png", x=x_univalle, y=y_logo, w=w_univalle)

        # Logo del centro (PSI)
        x_psi = x_univalle - espacio - w_psi
        self.image("recursos/psi.png", x=x_psi, y=y_logo, w=w_psi)

        # Logo izquierda (BuildScan App)
        x_app = x_psi - espacio - w_app
        self.image("recursos/logoApp.png", x=x_app, y=y_logo, w=w_app)

        y_logo = 10                
        logo_width = 20
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
        self.cell(0, 10, "Parámetros usados:", ln=True)
        self.set_font("Arial", size=11)

        if not params:
            self.cell(0, 10, f"Null: Nube subida desde archivo", ln=True)
            return
        
        for clave, valor in params.items():
            valor_texto = valor if valor is not None else "N/A"
            self.cell(0, 8, f"{clave.replace('_', ' ').capitalize()}: {valor_texto}", ln=True)


    def add_nube_3d_img(self, img_path):
        self.ln(5)
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "Visualización 3D:", ln=True)
        self.image(img_path, x=15, w=180)

    def add_info_nube(self, nombre, descripcion, fecha):
        self.ln(5)
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "Información de la nube:", ln=True)

        self.set_font("Arial", size=11)
        self.cell(0, 8, f"Nombre: {nombre}", ln=True)
        self.cell(0, 8, f"Descripción: {descripcion}", ln=True)
        self.cell(0, 8, f"Fecha de captura: {fecha}", ln=True)

    def add_las_info(self, las_path):
        self.set_font("Arial", size=12)
        self.ln(10)
        self.cell(0, 10, f"Nube en formato LAS: {os.path.basename(las_path)}", ln=True)
#--------------------------------------------------------------------

def renderizar_nube_con_matplotlib(pcd_path, out_img_path):
    pcd = o3d.io.read_point_cloud(pcd_path)
    puntos = np.asarray(pcd.points)

    if puntos.size == 0:
        raise ValueError("La nube de puntos está vacía")

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Ajuste del eje para vista más intuitiva (e.g. vista superior ligeramente inclinada)
    ax.scatter(puntos[:, 0], puntos[:, 1], puntos[:, 2],
               c=puntos[:, 2], cmap='viridis', s=0.5)

    ax.set_axis_off()

    # Vista ajustada
    ax.view_init(elev=70, azim=-90)  # Prueba con estos valores
    ax.dist = 10  # Controla el zoom
    plt.tight_layout()
    plt.savefig(out_img_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()


def convertir_a_las(pcd_path, out_path_las):
    nube = o3d.io.read_point_cloud(pcd_path)
    puntos = np.asarray(nube.points)

    header = laspy.LasHeader(point_format=3, version="1.2")
    las = laspy.LasData(header)
    las.x = puntos[:, 0]
    las.y = puntos[:, 1]
    las.z = puntos[:, 2]
    las.write(out_path_las)
