#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import rospy
import numpy as np
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2
import sensor_msgs.point_cloud2 as pc2

from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import QThread

import open3d as o3d

from telecomando_ui import Ui_Form
from APP_LIDAR.srv import LidarSweep
from datetime import datetime
from PyQt5.QtCore import pyqtSignal
from datetime import datetime

from PyQt5.QtCore import Qt

# ============================================================
# Hilo de movimiento
# ============================================================

class MovementThread(QThread):
    def __init__(self, pub):
        super().__init__()
        self.pub = pub
        self.running = True
        self.twist = Twist()

    def run(self):
        rate = rospy.Rate(10)
        while self.running and not rospy.is_shutdown():
            self.pub.publish(self.twist)
            rate.sleep()

    def update_twist(self, twist):
        self.twist = twist

    def stop(self):
        self.running = False


# ============================================================
# Widget principal
# ============================================================

class TelecomandoWidget(QWidget):
    cloud_received = pyqtSignal(object)
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        
        # UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # ROS init si aún no existe
        if not rospy.core.is_initialized():
            rospy.init_node("telecomando_gui", anonymous=True)

        # Publisher velocidad
        self.pub = rospy.Publisher('/RosAria/cmd_vel', Twist, queue_size=10)

        # Hilo de movimiento
        self.movement_thread = MovementThread(self.pub)
        self.movement_thread.start()

        # Suscribirse a odometría
        rospy.Subscriber('/odom', Odometry, self.odom_callback)

        # Suscribirse a la nube LIDAR proveniente del robot        
        self.pointcloud_sub = rospy.Subscriber("/lidar_cloud", PointCloud2, self.pointcloud_callback)

        self.received_cloud = None  # última nube recibida

        # Conectar botones
        self.ui.avanzarPushButton.pressed.connect(self.avanzar)
        self.ui.avanzarPushButton.released.connect(self.stop)
        self.ui.reversaPushButton.pressed.connect(self.retroceder)
        self.ui.reversaPushButton.released.connect(self.stop)
        self.ui.izquierdaPushButton.pressed.connect(self.izquierda)
        self.ui.izquierdaPushButton.released.connect(self.stop)
        self.ui.derechaPushButton.pressed.connect(self.derecha)
        self.ui.derechaPushButton.released.connect(self.stop)

        self.ui.iniciarOdomPushButton.clicked.connect(self.iniciar_odom)
        self.ui.finalizarOdomPushButton.clicked.connect(self.stop_odom)

        
        self.cloud_received.connect(self.mostrar_y_guardar_nube)

        # Botón de captura LIDAR
        self.ui.capturarPushButton.clicked.connect(self.llamar_captura)

        self.ui.logCapturaLabel.setText("🟢 Sistema listo.")

    # ============================================================
    # Movimiento
    # ============================================================

    def iniciar_odom(self):
        respuesta = QMessageBox.question(
            self,
            "Iniciar guardado de odometría",
            "¿Iniciar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes)

        if respuesta == QMessageBox.Yes:
            QMessageBox.information(
                self,
                "Registro de odometría",
                "Registro de odometría iniciado.")
        else:
            QMessageBox.information(
                self,
                "Registro de odometría",
                "Registro de odometría no iniciado.")
        return

    def stop_odom(self):
        respuesta = QMessageBox.question(
            self,
            "Detener guardado de odometría",
            "¿Detener?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes)

        if respuesta == QMessageBox.Yes:
            QMessageBox.information(
                self,
                "Registro de odometría",
                "Registro de odometría detenido.")
        else:
            QMessageBox.information(
                self,
                "Registro de odometría",
                "Registro de odometría no detenido.")
        return

    def get_linear_speed(self):
        return float(self.ui.velLineSpinBox.value())

    def get_angular_speed(self):
        return float(self.ui.velAnguSpinBox.value())

    def avanzar(self):
        t = Twist()
        t.linear.x = self.get_linear_speed()
        self.movement_thread.update_twist(t)

    def retroceder(self):
        t = Twist()
        t.linear.x = -self.get_linear_speed()
        self.movement_thread.update_twist(t)

    def izquierda(self):
        t = Twist()
        t.angular.z = self.get_angular_speed()
        self.movement_thread.update_twist(t)

    def derecha(self):
        t = Twist()
        t.angular.z = -self.get_angular_speed()
        self.movement_thread.update_twist(t)

    def stop(self):
        self.movement_thread.update_twist(Twist())

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_W:
            self.avanzar()
        elif key == Qt.Key_S:
            self.retroceder()
        elif key == Qt.Key_A:
            self.izquierda()
        elif key == Qt.Key_D:
            self.derecha()

        event.accept()

    def keyReleaseEvent(self, event):
        key = event.key()

        # detener solo si la tecla soltada es una de las WASD
        if key in (Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D):
            self.stop()

        event.accept()

    # ============================================================
    # Llamar servicio de captura
    # ============================================================

    def llamar_captura(self):
        try:
            steps = int(self.ui.stepsSpinBox.value())
            min_range = float(self.ui.rangoMinSpinBox.value())
            max_range = float(self.ui.rangoMaxSpinBox.value())
            fov = float(self.ui.fovSpinBox.value())
            prefix = self.ui.prefijoLineEdit.text().strip() or "barrido"
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Parámetros inválidos: {e}")
            return

        self.ui.logCapturaLabel.setText("📡 Llamando servicio /lidar_sweep...")        

        try:
            rospy.wait_for_service('/lidar_sweep')
            proxy = rospy.ServiceProxy('/lidar_sweep', LidarSweep)
            resp = proxy(steps, min_range, max_range, fov, prefix)

            if not resp.success:
                self.ui.logCapturaLabel.setText(f"❌ Error: {resp.message}")
                return

            self.ui.logCapturaLabel.setText("📨 Esperando nube publicada por el robot...")

        except Exception as e:
            self.ui.logCapturaLabel.setText(f"❌ Error al llamar servicio: {e}")

    # ============================================================
    # Recibir nube LIDAR publicada /lidar_points
    # ============================================================
    def pointcloud_callback(self, msg):
        try:
            pts = []
            for p in pc2.read_points(msg, skip_nans=True):
                pts.append([p[0], p[1], p[2]])

            if not pts:
                # emitir nube vacía igual
                self.cloud_received.emit(None)
                return

            cloud_np = np.array(pts)

            # Emitir la nube al hilo principal
            self.cloud_received.emit(cloud_np)

        except Exception as e:
            # Emitir error como None
            self.cloud_received.emit(None)

    def mostrar_y_guardar_nube(self, cloud_np):
        if cloud_np is None or len(cloud_np) == 0:
            self.ui.logCapturaLabel.setText("⚠️ Nube vacía o error al procesarla.")
            return

        try:
            # mostrar estado
            self.ui.logCapturaLabel.setText(f"✅ Nube recibida ({cloud_np.shape[0]} puntos). Abriendo visor...")

            # Convertir a Open3D
            cloud_o3d = o3d.geometry.PointCloud()
            cloud_o3d.points = o3d.utility.Vector3dVector(cloud_np)

            # Visualizar
            o3d.visualization.draw_geometries([cloud_o3d], window_name="Nube LIDAR")

            # Preguntar si guardar
            respuesta = QMessageBox.question(
                self,
                "Guardar nube",
                "¿Deseas guardar la nube capturada?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if respuesta == QMessageBox.Yes:
                prefix = self.ui.prefijoLineEdit.text().strip() or "nube"
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{prefix}_{timestamp}.pcd"

                o3d.io.write_point_cloud(filename, cloud_o3d)

                self.ui.logCapturaLabel.setText(f"💾 Nube guardada como: {filename}")
                QMessageBox.information(self, "Guardado", f"Nube guardada como\n{filename}")
            else:
                self.ui.logCapturaLabel.setText("🗑️ Nube descartada.")

        except Exception as e:
            self.ui.logCapturaLabel.setText(f"❌ Error mostrando/guardando nube: {e}")


    # ============================================================
    # Odometría
    # ============================================================

    def odom_callback(self, msg):
        pos = msg.pose.pose.position
        vel = msg.twist.twist

        txt = f"Pos: ({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f})\n"
        txt += f"Vel: L={vel.linear.x:.2f} m/s | A={vel.angular.z:.2f} rad/s"
        self.ui.posicionLabel.setText(txt)
    # ============================================================