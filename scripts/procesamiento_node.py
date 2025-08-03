from PyQt5.QtWidgets import QWidget, QMessageBox, QListWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from procesamiento_ui import Ui_Form
import requests
import open3d as o3d
import tempfile
import os
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
import io

from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QInputDialog

from parametros_node import ParametrosWidget

class ProcesamientoWidget(QWidget):
    def __init__(self, user_id, lista_nubes, actualizar_callback):
        super().__init__()
        self.user_id = user_id
        self.lista_nubes = lista_nubes
        self.actualizar_callback = actualizar_callback
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Asegurar layout para el visualizador
        self.plotter = QtInteractor(self.ui.vistaProcesamientoWidget)
        layout = QVBoxLayout()
        layout.addWidget(self.plotter.interactor)
        self.ui.vistaProcesamientoWidget.setLayout(layout)

        # Opcional: fondo blanco y configuración inicial
        self.plotter.set_background("white")

        # Conexiones
        self.ui.filtradoRuidoFrame.setVisible(False)
        self.ui.downsamplingFrame.setVisible(False)
        self.ui.segmentacionFrame.setVisible(False)
                
        self.ui.filtroRuidoCheckBox.stateChanged.connect(self.mostrar_filtrado_ruido)
        self.ui.downsamplingCheckBox.stateChanged.connect(self.mostrar_downsampling)
        self.ui.segmentacionCheckBox.stateChanged.connect(self.mostrar_segmentacion)
        self.ui.procesarNubePushButton.clicked.connect(self.aplicar_procesamiento)
        self.ui.guardarProcesadaPushButton.clicked.connect(self.guardar_nube_procesada)
        self.ui.borrarNubePushButton.clicked.connect(self.eliminar_nube)
        self.ui.subirNubePushButton.clicked.connect(self.subir_nube_puntos)


        self.param_widget = ParametrosWidget(user_id)

        self.cargar_lista_nubes()

#-----------------------------------------------------------------------------
    def actualizar_lista_externa(self, nueva_lista):
        self.lista_nubes = nueva_lista
        self.cargar_lista_nubes()
#-----------------------------------------------------------------------------

    def mostrar_filtrado_ruido(self, state):
        self.ui.filtradoRuidoFrame.setVisible(state == Qt.Checked)

    def mostrar_downsampling(self, state):
        self.ui.downsamplingFrame.setVisible(state == Qt.Checked)

    def mostrar_segmentacion(self, state):
        self.ui.segmentacionFrame.setVisible(state == Qt.Checked)

#-----------------------------------------------------------------------------

    def cargar_lista_nubes(self):
        self.ui.nubesListWidget.clear()
        for n in self.lista_nubes:
            item = QListWidgetItem(f"{n['nubeID']} - {n['nombre']}")
            item.setData(Qt.UserRole, n["nubeID"])
            self.ui.nubesListWidget.addItem(item)

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

                nombre, ok1 = QInputDialog.getText(self, "Guardar nube", "Nombre:")
                if not ok1 or not nombre:
                    return

                descripcion, ok2 = QInputDialog.getMultiLineText(self, "Guardar nube", "Descripción:")
                if not ok2:
                    return

                parametroID = self.param_widget.obtener_parametro_seleccionado()

                payload = {
                    "nombre": nombre,
                    "descripcion": descripcion,
                    "nombre_archivo": f"{nombre}.pcd",
                    "parametroID": parametroID
                }

                files = {
                    'archivo': (f"{nombre}.pcd", datos, 'application/octet-stream')
                }

                response = requests.post("http://127.0.0.1:5000/api/nube_puntos", files=files, data=payload)

                if response.status_code == 201:
                    QMessageBox.information(self, "Éxito", "Archivo subido correctamente.")
                    self.actualizar_callback()
                else:
                    QMessageBox.warning(self, "Error", response.text)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo subir el archivo: {str(e)}")

#-----------------------------------------------------------------------------
    def aplicar_procesamiento(self):
        items = self.ui.nubesListWidget.selectedItems()
        usar_alineacion = self.ui.alineacionCheckBox.isChecked()

        if not items:
            QMessageBox.warning(self, "Atención", "Selecciona al menos una nube para procesar.")
            return

        if usar_alineacion and len(items) != 2:
            QMessageBox.warning(self, "Atención", "Debes seleccionar exactamente DOS nubes para alineación.")
            return

        if not usar_alineacion and len(items) != 1:
            QMessageBox.warning(self, "Atención", "Debes seleccionar solo UNA nube para aplicar filtros.")
            return

        try:
            if usar_alineacion:
                id1 = items[0].data(Qt.UserRole)
                id2 = items[1].data(Qt.UserRole)

                pcd1 = self.procesar_nube(self.descargar_nube(id1))
                pcd2 = self.procesar_nube(self.descargar_nube(id2))

                if pcd1 is None or pcd2 is None:
                    QMessageBox.critical(self, "Error", "Error al procesar las nubes.")
                    return

                threshold = 30
                trans_init = np.eye(4)
                reg = o3d.pipelines.registration.registration_icp(
                    pcd2, pcd1, threshold, trans_init,
                    o3d.pipelines.registration.TransformationEstimationPointToPoint()
                )
                pcd2.transform(reg.transformation)
                resultado = pcd2
            else:
                nube_id = items[0].data(Qt.UserRole)
                resultado, planos_segmentados = self.procesar_nube(self.descargar_nube(nube_id))

            if resultado is None or len(resultado.points) == 0:
                QMessageBox.critical(self, "Error", "La nube procesada está vacía.")
                return

            self.resultado_pcd = resultado
            self.ultima_nube_procesada = resultado
            self.visualizar_pcd(resultado, planos_segmentados)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error durante el procesamiento: {str(e)}")

#-----------------------------------------------------------------------------

    def visualizar_pcd(self, pcd, planos_segmentados=None):
        puntos = np.asarray(pcd.points)
        if puntos.size == 0:
            QMessageBox.warning(self, "Visualización", "La nube de puntos está vacía.")
            return

        cloud = pv.PolyData(puntos)
        self.plotter.clear()

        if len(pcd.colors) > 0:
            colors = np.asarray(pcd.colors)
            cloud["RGB"] = (colors * 255).astype(np.uint8)
            self.plotter.add_mesh(
                cloud,
                scalars="RGB",
                rgb=True,
                point_size=3,
                render_points_as_spheres=True
            )
        else:
            z = puntos[:, 2]
            z -= z.min()
            cloud["altura"] = z
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

        if planos_segmentados:
            for idx, plano in enumerate(planos_segmentados):
                if len(plano.points) >= 3:
                    hull, _ = plano.compute_convex_hull()
                    hull_ls = o3d.geometry.LineSet.create_from_triangle_mesh(hull)
                    # Convertir los puntos y líneas a formato PyVista
                    puntos_hull = np.asarray(hull_ls.points)
                    lineas = np.asarray(hull_ls.lines)

                    # Construir conectividad de PyVista
                    cells = np.hstack([[2, *line] for line in lineas])
                    poly = pv.PolyData(puntos_hull, cells)
                    self.plotter.add_mesh(
                        poly,
                        color="black",
                        line_width=5,
                        render_lines_as_tubes=True
                    )

        self.plotter.reset_camera()
        self.plotter.render()

#-----------------------------------------------------------------------------

    def guardar_nube_procesada(self):
        if not hasattr(self, 'ultima_nube_procesada') or self.ultima_nube_procesada is None:
                QMessageBox.warning(self, "Atención", "No hay nube procesada para guardar.")
                return

        nombre, ok1 = QInputDialog.getText(self, "Guardar nube", "Nombre:")
        if not ok1 or not nombre:
            return

        descripcion, ok2 = QInputDialog.getMultiLineText(self, "Guardar nube", "Descripción:")
        if not ok2:
            return

        try:
            # Guardar temporalmente en formato .pcd
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pcd") as tmp_file:
                o3d.io.write_point_cloud(tmp_file.name, self.ultima_nube_procesada)
                tmp_file.seek(0)
                archivo_bytes = tmp_file.read()

            payload = {
                "nombre": nombre,
                "descripcion": descripcion,
                "nombre_archivo": f"{nombre}.pcd",
                "parametroID": self.param_widget.obtener_parametro_seleccionado()
            }

            files = {
                'archivo': (f"{nombre}.pcd", archivo_bytes, 'application/octet-stream')
            }

            response = requests.post("http://127.0.0.1:5000/api/nube_puntos", data=payload, files=files)

            if response.status_code == 201:
                QMessageBox.information(self, "Éxito", "Nube procesada guardada exitosamente.")
                self.actualizar_callback()
            else:
                QMessageBox.critical(self, "Error", f"No se pudo guardar: {response.text}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar la nube: {str(e)}")

#-----------------------------------------------------------------------------

    def descargar_nube(self, nube_id):
        try:
            response = requests.get(f"http://127.0.0.1:5000/api/nube_puntos/{nube_id}")
            if response.status_code != 200:
                QMessageBox.warning(self, "Error", "No se pudo descargar la nube.")
                return None

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pcd") as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            pcd = o3d.io.read_point_cloud(tmp_path)
            os.remove(tmp_path)
            return pcd
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al descargar nube: {str(e)}")
            return None

#-----------------------------------------------------------------------------

    def procesar_nube(self, pcd):
        planos_segmentados = []

        if self.ui.filtroRuidoCheckBox.isChecked():
            vecinos = int(self.ui.vecinosSpinBox.value())
            std_dev = float(self.ui.devStdSpinBox.value())
            pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=vecinos, std_ratio=std_dev)

        if self.ui.downsamplingCheckBox.isChecked():
            voxel_size = float(self.ui.voxelSizeSpinBox.value())
            pcd = pcd.voxel_down_sample(voxel_size=voxel_size)

        if self.ui.segmentacionCheckBox.isChecked():
            num_planos = int(self.ui.numPlanosSpinBox.value())
            distancia = float(self.ui.distanciaSpinBox.value())
            iteraciones = int(self.ui.iteracionesSpinBox.value())
            resto = pcd
            planos = []
            colors = [[1, 0, 1], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 0], [0, 1, 1]]

            for i in range(num_planos):
                plane_model, inliers = resto.segment_plane(
                    distance_threshold=distancia,
                    ransac_n=3,
                    num_iterations=iteraciones
                )
                inlier_cloud = resto.select_by_index(inliers)
                inlier_cloud.paint_uniform_color(colors[i % len(colors)])
                planos_segmentados.append(inlier_cloud)
                planos.append(inlier_cloud)
                resto = resto.select_by_index(inliers, invert=True)

            pcd = planos[0]
            for plano in planos[1:]:
                pcd += plano

        return pcd, planos_segmentados

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
                    self.actualizar_callback()  # actualiza listas en ambos módulos
                else:
                    QMessageBox.warning(self, "Error", f"No se pudo eliminar la nube: {response.text}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar: {str(e)}")
