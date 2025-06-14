# login_node.py

from PyQt5.QtWidgets import QWidget, QMessageBox, QLineEdit
from login_ui import Ui_loginWindow
import sqlite3, os
import requests 

class LoginWindow(QWidget):
    def __init__(self, switch_window_callback):
        super().__init__()
        self.ui = Ui_loginWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("Login")

        self.ui.passwordLineEdit.setEchoMode(QLineEdit.Password)

        self.ui.confirmButton.clicked.connect(self.attempt_login)
        self.switch_window = switch_window_callback

    def attempt_login(self):
        user = self.ui.usernameLineEdit.text()
        pwd = self.ui.passwordLineEdit.text()

        try:
            response = requests.post("http://127.0.0.1:5000/api/login", json={
                "username": user,
                "password": pwd
            })

            if response.status_code == 200:
                data = response.json()
                user_id = data.get("userID")  
                self.switch_window(user_id)   
                self.close()

            elif response.status_code == 401:
                QMessageBox.warning(self, "Error", "Credenciales inválidas")
            else:
                QMessageBox.critical(self, "Error", f"Error del servidor: {response.json().get('message')}")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"No se pudo conectar al servidor API:\n{str(e)}")
