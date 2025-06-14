# main.py

import sys
import os
from PyQt5.QtWidgets import QApplication
from login_node import LoginWindow
from main_window_node import MainWindow
from user_registration_node import UserRegistrationWidget

class AppController:
    def __init__(self):
        self.login_window = None
        self.main_window = None        

    def show_login(self):
        self.login_window = LoginWindow(self.show_main_window)
        self.login_window.show()

    def show_main_window(self, user_id):
        self.main_window = MainWindow(user_id = user_id)
        self.main_window.show()        
        self.login_window.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = AppController()
    controller.show_login()
    sys.exit(app.exec_())
