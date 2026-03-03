# parametros_node.py

from PyQt5.QtWidgets import QWidget, QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt
from tomlkit import item
from parametros_ui import Ui_Form
import requests

class ParametrosWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.parametro_id = None
          
        self.ui.confirmarPushButton.clicked.connect(self.save_parametros)
        self.ui.loadDefaultsButton.clicked.connect(self.cargar_parametros_por_defecto)
        self.ui.presetsListWidget.itemClicked.connect(self.seleccionar_preset)
        self.ui.nuevoPresetButton.clicked.connect(self.nuevo_preset)
        self.ui.eliminarPresetpushButton.clicked.connect(self.eliminar_preset)

        self.load_parametros()

#----------------------------------------------------------------------------------

    def save_parametros(self):
        data = {
            "usuario_id": self.user_id,
            "nombre_preset": self.ui.nombrePresetLineEdit.text(),
            "descripcion": self.ui.descripcionTextEdit.toPlainText(),
            
            "velocidad_lineal": self.ui.velLineSpinBox.value(),
            "velocidad_angular": self.ui.velAnguSpinBox.value(),


            # Captura de nubes
            "num_steps": self.ui.stepsSpinBox.value(),
            "max_range": self.ui.rangoMaxSpinBox.value(),
            "min_range": self.ui.rangoMinSpinBox.value(),
            "fov_angel": self.ui.fovSpinBox.value(),
            "prefijo": self.ui.prefijoLineEdit.text(),
            # preprocesamiento
            "vecinos": self.ui.vecinosSpinBox.value(),
            "dev_std": self.ui.devStdSpinBox.value(),
            "z_max": self.ui.zMaxSpinBox.value(),
            "z_min": self.ui.zMinSpinBox.value(),
            "voxel_size": self.ui.voxelSizeSpinBox.value(),

            # procesamiento
            "num_planos": self.ui.numPlanosSpinBox.value(),
            "distancia": self.ui.distanciaSpinBox.value(),
            "iteraciones": self.ui.iteracionesSpinBox.value(),

            # alineacion
            "voxel_size_ali": self.ui.voxelSizeAlineacionSpinBox.value(),
            "normal_rad": self.ui.normalRadSpinBox.value(),
            "normal_max_nn": self.ui.normalMaxNnSpinBox.value(),
            "fpfh_rad": self.ui.fpfhRadSpinBox.value(),
            "fpfh_max_nn": self.ui.fpfhMaxNnSpinBox.value()  
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
                self.load_parametros() 
                # self.limpiar_formulario()
            else:
                QMessageBox.warning(self, "Error", response.text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")

#----------------------------------------------------------------------------------

    def load_parametros(self):        
        try:
            response = requests.get(f"http://127.0.0.1:5000/api/parametros/por_usuario/{self.user_id}")
            if response.status_code == 200:
                parametros_list = response.json().get("parametros", []) 

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
                self.ui.descripcionTextEdit.setText(defaults.get("descripcion", ""))                
                self.ui.velLineSpinBox.setValue(defaults.get("velocidad_lineal", 0.0))
                self.ui.velAnguSpinBox.setValue(defaults.get("velocidad_angular", 0.0))

                # Captura de nubes
                self.ui.stepsSpinBox.setValue(defaults.get("num_steps", 0))
                self.ui.rangoMaxSpinBox.setValue(defaults.get("max_range", 0))
                self.ui.rangoMinSpinBox.setValue(defaults.get("min_range", 0))
                self.ui.fovSpinBox.setValue(defaults.get("fov_angel", 0))
                self.ui.prefijoLineEdit.setText(defaults.get("prefijo", ""))
                # preprocesamiento
                self.ui.vecinosSpinBox.setValue(defaults.get("vecinos", 0))
                self.ui.devStdSpinBox.setValue(defaults.get("dev_std", 0))
                self.ui.zMaxSpinBox.setValue(defaults.get("z_max", 0))
                self.ui.zMinSpinBox.setValue(defaults.get("z_min", 0))
                self.ui.voxelSizeSpinBox.setValue(defaults.get("voxel_size", 0.0))
                # procesamiento
                self.ui.numPlanosSpinBox.setValue(defaults.get("num_planos", 0))
                self.ui.distanciaSpinBox.setValue(defaults.get("distancia", 0.0))
                self.ui.iteracionesSpinBox.setValue(defaults.get("iteraciones", 0))
                # alineacion
                self.ui.voxelSizeAlineacionSpinBox.setValue(defaults.get("voxel_size_ali", 0.0))
                self.ui.normalRadSpinBox.setValue(defaults.get("normal_rad", 0.0))
                self.ui.normalMaxNnSpinBox.setValue(defaults.get("normal_max_nn", 0))
                self.ui.fpfhRadSpinBox.setValue(defaults.get("fpfh_rad", 0))
                self.ui.fpfhMaxNnSpinBox.setValue(defaults.get("fpfh_max_nn", 0))

                QMessageBox.information(self, "Info", "Parámetros por defecto cargados.")
            else:
                QMessageBox.warning(self, "Error", "No se pudieron cargar los parámetros por defecto.")                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")

#----------------------------------------------------------------------------------

    def seleccionar_preset(self, item):        
        parametro_id = item.data(Qt.UserRole)
        self.parametro_id = parametro_id         

        try:
            response = requests.get(f"http://127.0.0.1:5000/api/parametros/{parametro_id}")
            if response.status_code == 200:
                p = response.json().get("parametros", {})

                self.ui.nombrePresetLineEdit.setText(p.get("nombre_preset", ""))
                self.ui.descripcionTextEdit.setText(p.get("descripcion", ""))                
                self.ui.velLineSpinBox.setValue(p.get("velocidad_lineal", 0.0))
                self.ui.velAnguSpinBox.setValue(p.get("velocidad_angular", 0.0))

                # Captura de nubes
                self.ui.stepsSpinBox.setValue(p.get("num_steps", 0))
                self.ui.rangoMaxSpinBox.setValue(p.get("max_range", 0))
                self.ui.rangoMinSpinBox.setValue(p.get("min_range", 0))
                self.ui.fovSpinBox.setValue(p.get("fov_angel", 0))
                self.ui.prefijoLineEdit.setText(p.get("prefijo", ""))
                # preprocesamiento
                self.ui.vecinosSpinBox.setValue(p.get("vecinos", 0))
                self.ui.devStdSpinBox.setValue(p.get("dev_std", 0))
                self.ui.zMaxSpinBox.setValue(p.get("z_max", 0))
                self.ui.zMinSpinBox.setValue(p.get("z_min", 0))
                self.ui.voxelSizeSpinBox.setValue(p.get("voxel_size", 0.0))
                # procesamiento
                self.ui.numPlanosSpinBox.setValue(p.get("num_planos", 0))
                self.ui.distanciaSpinBox.setValue(p.get("distancia", 0.0))
                self.ui.iteracionesSpinBox.setValue(p.get("iteraciones", 0))
                # alineacion
                self.ui.voxelSizeAlineacionSpinBox.setValue(p.get("voxel_size_ali", 0.0))
                self.ui.normalRadSpinBox.setValue(p.get("normal_rad", 0.0))
                self.ui.normalMaxNnSpinBox.setValue(p.get("normal_max_nn", 0))
                self.ui.fpfhRadSpinBox.setValue(p.get("fpfh_rad", 0))
                self.ui.fpfhMaxNnSpinBox.setValue(p.get("fpfh_max_nn", 0))
                # TODO: cargar el resto de campos
            else:
                QMessageBox.warning(self, "Error", "No se pudo cargar el preset seleccionado.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")

#-----------------------------------------------------------------------------

    def nuevo_preset(self):        
        self.parametro_id = None  
        self.ui.nombrePresetLineEdit.clear()
        self.ui.descripcionTextEdit.clear()        
        self.ui.velLineSpinBox.setValue(0.0)
        self.ui.velAnguSpinBox.setValue(0.0)
        
        # Captura de nubes
        self.ui.stepsSpinBox.setValue(0.0)
        self.ui.rangoMaxSpinBox.setValue(0)
        self.ui.rangoMinSpinBox.setValue(0)
        self.ui.fovSpinBox.setValue(0)
        self.ui.prefijoLineEdit.clear()
        # preprocesamiento
        self.ui.vecinosSpinBox.setValue(0)
        self.ui.devStdSpinBox.setValue(0)
        self.ui.zMaxSpinBox.setValue(0)
        self.ui.zMinSpinBox.setValue(0)
        self.ui.voxelSizeSpinBox.setValue(0.0)
        # procesamiento
        self.ui.numPlanosSpinBox.setValue(0)
        self.ui.distanciaSpinBox.setValue(0.0)
        self.ui.iteracionesSpinBox.setValue(0)
        # alineacion
        self.ui.voxelSizeAlineacionSpinBox.setValue(0.0)
        self.ui.normalRadSpinBox.setValue(0.0)
        self.ui.normalMaxNnSpinBox.setValue(0)
        self.ui.fpfhRadSpinBox.setValue(0)
        self.ui.fpfhMaxNnSpinBox.setValue(0)

        self.ui.presetsListWidget.clearSelection() 

#---------------------------------------------------------------------------------

    def eliminar_preset(self):
        if not self.parametro_id:
            QMessageBox.warning(self, "Aviso", "No hay preset seleccionado para eliminar.")
            return

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
                self.nuevo_preset()   
                self.load_parametros()  
            else:
                QMessageBox.warning(self, "Error", response.text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al conectar: {str(e)}")

#----------------------------------------------------------------------------------

    def obtener_parametro_seleccionado(self):        
        if self.parametro_id != None:            
            return self.parametro_id
        else:
            return None
