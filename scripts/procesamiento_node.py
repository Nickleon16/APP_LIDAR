# procesamiento_node.py

from PyQt5.QtWidgets import QWidget, QMessageBox, QListWidgetItem, QFileDialog
from PyQt5.QtCore import Qt
from procesamiento_ui import Ui_Form
import requests
import open3d as o3d
import tempfile
import subprocess
import os

class ProcesamientoWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.filtradoRuidoFrame.setVisible(False)
        self.ui.downsamplingFrame.setVisible(False)
        self.ui.segmentacionFrame.setVisible(False)

        self.ui.actualizarListaPushButton.clicked.connect(self.cargar_lista_nubes)  

        self.ui.filtroRuidoCheckBox.stateChanged.connect(self.mostrar_filtrado_ruido)
        self.ui.downsamplingCheckBox.stateChanged.connect(self.mostrar_downsampling)
        self.ui.segmentacionCheckBox.stateChanged.connect(self.mostrar_segmentacion)

        self.ui.procesarNubePushButton.clicked.connect(self.aplicar_procesamiento)

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

    def aplicar_procesamiento(self):
        item = self.ui.nubesListWidget.currentItem()
        if not item:
            QMessageBox.warning(self, "Atención", "Selecciona una nube para procesar.")
            return

        nube_id = item.data(Qt.UserRole)        

        try:            
            response = requests.get(f"http://127.0.0.1:5000/api/nube_puntos/{nube_id}")
            if response.status_code != 200:
                QMessageBox.warning(self, "Error", "No se pudo descargar la nube.")
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pcd") as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            pcd = o3d.io.read_point_cloud(tmp_path)
            procesado_bool = False
#------------------------------------------------------------------------------            
            # Filtro de ruido
            if self.ui.filtroRuidoCheckBox.isChecked():       
                procesado_bool = True         
                vecinos = int(self.ui.vecinosSpinBox.value())
                std_dev = float(self.ui.devStdSpinBox.value())
                pcd_procesada, _ = pcd.remove_statistical_outlier(nb_neighbors=vecinos, std_ratio=std_dev)
#------------------------------------------------------------------------------
            # Downsampling
            if self.ui.downsamplingCheckBox.isChecked():
                if procesado_bool == False:
                    pcd_procesada = pcd

                procesado_bool = True
                voxel_size = float(self.ui.voxelSizeSpinBox.value())
                pcd_procesada = pcd_procesada.voxel_down_sample(voxel_size=voxel_size)
#------------------------------------------------------------------------------
            if self.ui.segmentacionCheckBox.isChecked():                
                
                if procesado_bool == False:
                    resto = pcd
                else:
                    resto = pcd_procesada
                
                procesado_bool = True
            
                num_planos = int(self.ui.numPlanosSpinBox.value())
                distancia = float(self.ui.distanciaSpinBox.value())
                iteraciones = int(self.ui.iteracionesSpinBox.value())   
                
                planes = []
                colors = [[1, 0, 1], [0, 1, 0], [0, 0, 1], [1, 1, 0]]

                for i in range(num_planos):
                    plane_model, inliers = resto.segment_plane(
                        distance_threshold=distancia,
                        ransac_n=3,
                        num_iterations=iteraciones
                    )

                    inlier_cloud = resto.select_by_index(inliers)
                    inlier_cloud.paint_uniform_color(colors[i % len(colors)])
                    planes.append(inlier_cloud)

                    # Quitar plano segmentado
                    resto = resto.select_by_index(inliers, invert=True)

                nube_segmentada = planes[0]
                for p in planes[1:]:
                    nube_segmentada += p
                
                pcd_procesada = nube_segmentada
                #o3d.visualization.draw_geometries(planes + [resto])
#------------------------------------------------------------------------------

            os.remove(tmp_path) 
            # Guardar nube procesada temporalmente para visualizar
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pcd") as tmp_out:
                o3d.io.write_point_cloud(tmp_out.name, pcd_procesada)
                path_resultado = tmp_out.name

            # Llamar al visualizador externo
            subprocess.Popen(["python3", "visualizador_nubes.py", path_resultado])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al procesar la nube: {str(e)}")