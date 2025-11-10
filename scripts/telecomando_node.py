#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import signal
from datetime import datetime

import rospy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox

import open3d as o3d
from telecomando_ui import Ui_Form


# ---------------------------------------------------------------------
# Thread para ejecutar el proceso externo de captura
# ---------------------------------------------------------------------
class CaptureProcessThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)  # Código de salida

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd
        self.process = None
        self.running = True

    def run(self):
        try:
            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
            )

            # Leer la salida en tiempo real
            for line in self.process.stdout:
                if not self.running:
                    break
                self.log_signal.emit(line.strip())

            self.process.wait()
            self.finished_signal.emit(self.process.returncode)

        except Exception as e:
            self.log_signal.emit(f"❌ Error ejecutando captura: {e}")
            self.finished_signal.emit(-1)

    def stop(self):
        self.running = False
        if self.process and self.process.poll() is None:
            self.process.send_signal(signal.SIGINT)
            self.log_signal.emit("🛑 Captura detenida.")
        self.quit()
        self.wait()


# ---------------------------------------------------------------------
# Widget principal (telecomando + captura)
# ---------------------------------------------------------------------
class TelecomandoWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Inicializar ROS
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.rate = rospy.Rate(10)

        # Estado inicial
        self.capture_thread = None
        self.ui.logCapturaLabel.setText("🟢 Sistema listo.")

        # Configuración de parámetros de velocidad
        self.speed = 0.2
        self.turn = 1.0

        # Conexión de botones de movimiento
        self.ui.avanzarPushButton.pressed.connect(self.avanzar)
        self.ui.avanzarPushButton.released.connect(self.stop)
        self.ui.reversaPushButton.pressed.connect(self.retroceder)
        self.ui.reversaPushButton.released.connect(self.stop)
        self.ui.izquierdaPushButton.pressed.connect(self.izquierda)
        self.ui.izquierdaPushButton.released.connect(self.stop)
        self.ui.derechaPushButton.pressed.connect(self.derecha)
        self.ui.derechaPushButton.released.connect(self.stop)

        # Botón de captura
        self.ui.capturarPushButton.clicked.connect(self.iniciar_captura)

        # Subscripciones ROS
        rospy.Subscriber('/odom', Odometry, self.odom_callback)

    # ------------------- Movimiento -------------------
    def avanzar(self): self.publish_speed(self.speed)
    def retroceder(self): self.publish_speed(-self.speed)
    def izquierda(self): self.publish_turn(self.turn)
    def derecha(self): self.publish_turn(-self.turn)
    def stop(self): self.pub.publish(Twist())

    def publish_speed(self, v):
        twist = Twist()
        twist.linear.x = v
        self.pub.publish(twist)

    def publish_turn(self, w):
        twist = Twist()
        twist.angular.z = w
        self.pub.publish(twist)
    
    # ------------------- Captura -------------------
    def iniciar_captura(self):
        # Si ya está corriendo, detener
        if self.capture_thread and self.capture_thread.isRunning():
            self.capture_thread.stop()
            self.capture_thread = None
            self.ui.capturarPushButton.setText("Iniciar Captura")
            return

        try:
            # === Leer parámetros desde la GUI ===
            steps = int(self.ui.stepsSpinBox.value())   # Nuevo control en GUI
            min_range = float(self.ui.rangoMinSpinBox.value())
            max_range = float(self.ui.rangoMaxSpinBox.value())
            fov = float(self.ui.fovSpinBox.value())
            prefix = self.ui.prefijoLineEdit.text().strip() or "barrido"

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Parámetros inválidos: {e}")
            return

        # === Llamar script con --steps ===
        cmd = [
            "python3", "captura_lidar.py",
            "--min_range", str(min_range),
            "--max_range", str(max_range),
            "--steps", str(steps),
            "--fov", str(fov),
            "--prefix", prefix
        ]

        self.ui.logCapturaLabel.setText("📸 Iniciando captura...")
        self.ui.capturarPushButton.setText("Detener Captura")

        # Lanzar hilo
        self.capture_thread = CaptureProcessThread(cmd)
        self.capture_thread.log_signal.connect(self.log_message)
        self.capture_thread.finished_signal.connect(self.captura_finalizada)
        self.capture_thread.start()


    def log_message(self, msg):
        self.ui.logCapturaLabel.setText(msg)

    def captura_finalizada(self, code):
        self.ui.capturarPushButton.setText("Iniciar Captura")
        self.capture_thread = None

        if code != 0:
            self.ui.logCapturaLabel.setText(f"⚠️ Captura terminada con código {code}.")
            return

        self.ui.logCapturaLabel.setText("✅ Captura finalizada correctamente.")

        temp_file = "temp_cloud.pcd"
        if not os.path.exists(temp_file):
            QMessageBox.warning(self, "Error", "No se encontró la nube temporal generada.")
            return

        # Mostrar nube en visualizador Open3D
        try:
            cloud = o3d.io.read_point_cloud(temp_file)
            if len(cloud.points) == 0:
                QMessageBox.warning(self, "Nube vacía", "La nube generada está vacía.")
                return

            self.ui.logCapturaLabel.setText("👁️ Mostrando nube capturada...")
            o3d.visualization.draw_geometries([cloud], window_name="Vista de Nube LIDAR")

        except Exception as e:
            QMessageBox.warning(self, "Error visualizando nube", str(e))
            return

        # Preguntar si se desea guardar
        respuesta = QMessageBox.question(
            self,
            "Guardar nube",
            "¿Deseas guardar la nube capturada?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if respuesta == QMessageBox.Yes:
            prefix = self.ui.prefijoLineEdit.text().strip() or "barrido"
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_path = f"{prefix}_{now}.pcd"
            os.rename(temp_file, final_path)
            QMessageBox.information(self, "Guardado", f"Nube guardada como {final_path}")
        else:
            os.remove(temp_file)
            QMessageBox.information(self, "Descartado", "La nube fue eliminada.")

    # ------------------- Callbacks ROS -------------------
    def odom_callback(self, msg):
        pos = msg.pose.pose.position
        vel = msg.twist.twist
        texto = f"Pos: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})\n"
        texto += f"Vel: L={vel.linear.x:.2f} m/s | A={vel.angular.z:.2f} rad/s"
        self.ui.posicionLabel.setText(texto)
