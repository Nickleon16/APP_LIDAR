# user_registration_node.py

import sys
import os
import threading
import requests
import rospy
from PyQt5.QtWidgets import QApplication, QWidget
from user_registration_ui import Ui_UserRegistration  
from PyQt5.QtWidgets import QTableWidgetItem
import ast 
from PyQt5.QtWidgets import QMessageBox

class UserRegistrationWidget(QWidget):
    def __init__(self):
        super(UserRegistrationWidget, self).__init__()
        self.ui = Ui_UserRegistration()
        self.ui.setupUi(self)
        self.editing_user_id = None

        # Conectar los botones
        self.ui.registerButton.clicked.connect(self.register_user)
        self.ui.clearButton.clicked.connect(self.clear_fields)
        self.ui.editarButton.clicked.connect(self.on_edit_button_clicked)
        self.ui.borrarButton.clicked.connect(self.on_delete_button_clicked)

        #self.ui.tableWidget.cellClicked.connect(self.on_row_selected)

#----------------------------------------------------------------------------------

    def on_edit_button_clicked(self):
        selected_row = self.ui.tableWidget.currentRow()
        if selected_row >= 0:
            self.load_user_to_form(selected_row)

#----------------------------------------------------------------------------------

    def register_user(self):
        name = self.ui.nameLineEdit.text()
        email = self.ui.emailLineEdit.text()
        username = self.ui.usernameLineEdit.text()
        password = self.ui.passwordLineEdit.text()
        confirm = self.ui.confirmLineEdit.text()

        admin = self.ui.adminRadioButton.isChecked()
        operario = self.ui.operaRadioButton.isChecked()
        rol = "Administrador" if admin else "Operario"

        activo = self.ui.activoRadioButton.isChecked()
        inactivo = self.ui.inactivoRadioButton.isChecked()
        status = "Activo" if activo else "No activo"

        if (activo and inactivo) or (admin and operario):
            self.ui.statusLabel.setText("Selecciona solo un rol y un estado.")
            return

        if not all([name, email, username, rol, status]):
            self.ui.statusLabel.setText("Completa todos los campos.")
            return

        if self.editing_user_id is None and (not password or not confirm):
            self.ui.statusLabel.setText("Contraseña requerida.")
            return

        if password != confirm:
            self.ui.statusLabel.setText("¡Las contraseñas no coinciden!")
            return

        data = {
            "nombre": name,
            "email": email,
            "username": username,
            "rol": rol,
            "status": status
        }

        if password:
            data["password"] = password

        try:
            if self.editing_user_id:
                url = f"http://localhost:5000/api/usuarios/{self.editing_user_id}"
                response = requests.put(url, json=data)                
            else:
                url = "http://localhost:5000/api/usuarios"
                response = requests.post(url, json=data)                

            if response.status_code in (200, 201):
                self.ui.statusLabel.setText("Usuario actualizado." if self.editing_user_id else "Usuario registrado.")
                self.clear_fields()
                self.load_users()
            else:
                try:
                    error_msg = response.json().get("error", "Error desconocido")
                except ValueError:
                    error_msg = response.text or "Respuesta vacía del servidor"

                self.ui.statusLabel.setText(f"Error: {error_msg}")

        except Exception as e:
            self.ui.statusLabel.setText(f"Error al conectar: {str(e)}")

#----------------------------------------------------------------------------------

    def clear_fields(self):
        self.ui.nameLineEdit.clear()
        self.ui.emailLineEdit.clear()
        self.ui.usernameLineEdit.clear()
        self.ui.passwordLineEdit.clear()
        self.ui.confirmLineEdit.clear()
        self.ui.statusLabel.clear()
        self.editing_user_id = None  

        self.ui.adminRadioButton.setChecked(False)
        self.ui.operaRadioButton.setChecked(False)
        self.ui.activoRadioButton.setChecked(False)
        self.ui.inactivoRadioButton.setChecked(False)


#----------------------------------------------------------------------------------

    def load_users(self):
        try:
            response = requests.get("http://localhost:5000/api/usuarios")
            if response.status_code == 200:
                raw_usuarios = response.json().get("usuarios", [])
                
                if isinstance(raw_usuarios, str):
                    self.users = ast.literal_eval(raw_usuarios)
                else:
                    self.users = raw_usuarios

                self.ui.tableWidget.setRowCount(len(self.users))
                self.ui.tableWidget.setColumnCount(3)
                self.ui.tableWidget.setHorizontalHeaderLabels(["ID", "Name", "Username"])

                for row, user in enumerate(self.users):
                    self.ui.tableWidget.setItem(row, 0, QTableWidgetItem(str(user["userID"])))
                    self.ui.tableWidget.setItem(row, 1, QTableWidgetItem(user["nombre"]))
                    self.ui.tableWidget.setItem(row, 2, QTableWidgetItem(user["username"]))
            else:
                self.ui.statusLabel.setText("Error al cargar usuarios.")
        except Exception as e:
            self.ui.statusLabel.setText(f"Error: {str(e)}")


#----------------------------------------------------------------------------------

    def load_user_to_form(self, row):
        user_id_item = self.ui.tableWidget.item(row, 0)
        if not user_id_item:
            return
        user_id = user_id_item.text()

        user = next((u for u in self.users if str(u["userID"]) == user_id), None)
        if not user:
            return

        self.editing_user_id = user["userID"]  

        # Cargar datos
        self.ui.nameLineEdit.setText(user.get("nombre", ""))
        self.ui.emailLineEdit.setText(user.get("email", ""))
        self.ui.usernameLineEdit.setText(user.get("username", ""))
        
        self.ui.passwordLineEdit.setText("")
        self.ui.confirmLineEdit.setText("")

        # Rol
        self.ui.adminRadioButton.setChecked(user.get("rol") == "Administrador")
        self.ui.operaRadioButton.setChecked(user.get("rol") == "Operario")

        # Estado
        self.ui.activoRadioButton.setChecked(user.get("status") == "Activo")
        self.ui.inactivoRadioButton.setChecked(user.get("status") == "No activo")

#----------------------------------------------------------------------------------

    def on_delete_button_clicked(self):
        selected_row = self.ui.tableWidget.currentRow()
        if selected_row < 0:
            self.ui.statusLabel.setText("Selecciona un usuario para borrar.")
            return

        user_id_item = self.ui.tableWidget.item(selected_row, 0)
        name_item = self.ui.tableWidget.item(selected_row, 1)

        if user_id_item and name_item:
            user_id = user_id_item.text()
            user_name = name_item.text()

            confirm = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Estás seguro de que deseas eliminar al usuario '{user_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )

            if confirm == QMessageBox.Yes:
                try:
                    response = requests.delete(f"http://localhost:5000/api/usuarios/{user_id}")
                    if response.status_code == 200:
                        self.ui.statusLabel.setText("Usuario eliminado exitosamente.")
                        self.load_users()
                        self.clear_fields()
                    else:
                        self.ui.statusLabel.setText(f"Error al eliminar: {response.json().get('error')}")
                except Exception as e:
                    self.ui.statusLabel.setText(f"Error al conectar: {str(e)}")

#----------------------------------------------------------------------------------

def main():
    rospy.init_node('user_registration_gui', anonymous=True)
    threading.Thread(target=rospy.spin, daemon=True).start()

    app = QApplication(sys.argv)
    widget = UserRegistrationWidget()
    widget.show()
    widget.load_users()  
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
