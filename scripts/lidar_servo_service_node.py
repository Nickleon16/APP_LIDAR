#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lidar + servo scanner corregido para eje de giro en X y offset físico entre eje y centro del LIDAR.
- Calibración ticks->deg con 3 puntos.
- move_servo espera la posición real.
- Aplica traslación (dx,dy,dz) antes de rotar alrededor de X.
"""

import os
import math
import json
import rospy
import numpy as np
from sensor_msgs.msg import LaserScan, PointCloud2
import sensor_msgs.point_cloud2 as pc2
from std_msgs.msg import Header
from dynamixel_sdk import *
from APP_LIDAR.srv import LidarSweep, LidarSweepResponse
from sensor_msgs.msg import PointCloud2, PointField

# ==== CONFIGURACIÓN SERVO ====
DEVICENAME = '/dev/ttyUSB1'
BAUDRATE = 57600
PROTOCOL_VERSION = 1.0
DXL_ID = 1
ADDR_TORQUE_ENABLE     = 24
ADDR_GOAL_POSITION     = 30
ADDR_PRESENT_POSITION  = 36
TORQUE_ENABLE          = 1
TORQUE_DISABLE         = 0

# ==== CALIBRACIÓN (ticks reales proporcionados) ====
TICKS_NEG90   = 2570.0   # corresponde a -90°
TICKS_CENTER  = 1543.0   # reposo ≈ 0°
TICKS_POS90   = 520.0    # corresponde a +90°

# ==== OFFSET FÍSICO entre EJE DEL SERVO y el centro del LIDAR (metros) ====
# Según foto / medida: 5 cm hacia adelante (+X), 0 lateral, 2 cm arriba (+Z)
DX = 0.08  # m hacia adelante (X)
DY = 0.04    # m lateral (Y)
DZ = 0.00  # m arriba (Z)
OFFSET = np.array([DX, DY, DZ], dtype=float)

# Parámetros de espera/timeout (ajustables)
DEFAULT_MOVE_TIMEOUT = 1.0   # segundos
DEFAULT_MOVE_TOLERANCE_TICKS = 8

def numpy_to_pointcloud2(points, frame_id="lidar_link"):
    if isinstance(points, np.ndarray):
        pts_list = points.tolist()
    else:
        pts_list = list(points)
    fields = [
        PointField('x', 0, PointField.FLOAT32, 1),
        PointField('y', 4, PointField.FLOAT32, 1),
        PointField('z', 8, PointField.FLOAT32, 1)
    ]
    header = Header()
    header.stamp = rospy.Time.now()
    header.frame_id = frame_id
    return pc2.create_cloud(header, fields, pts_list)

def ticks_to_angle(ticks):
    """
    Interpola ticks -> grados usando los 3 puntos calibrados.
    np.interp necesita xp ordenado ascendentemente, así que lo ordenamos.
    """
    xp = np.array([TICKS_NEG90, TICKS_CENTER, TICKS_POS90], dtype=float)
    fp = np.array([-90.0, 0.0, 90.0], dtype=float)
    order = np.argsort(xp)
    xp_sorted = xp[order]
    fp_sorted = fp[order]
    return float(np.interp(float(ticks), xp_sorted, fp_sorted))

class LidarServoScanner:
    def __init__(self, steps=11, min_range=0.05, max_range=5.0, fov=360.0, prefix="barrido"):
        self.steps = steps
        self.min_range = min_range
        self.max_range = max_range
        self.fov = fov
        self.prefix = prefix

        self.latest_scan = None
        self.points_all = []

        # ROS subscribers/publishers (no init_node aquí)
        rospy.Subscriber("/scan", LaserScan, self.scan_callback)
        self.slice_pub = rospy.Publisher("/lidar_slice", PointCloud2, queue_size=1)
        self.cloud_pub = rospy.Publisher("/lidar_cloud", PointCloud2, queue_size=1)

        # Esperar al primer scan
        while self.latest_scan is None and not rospy.is_shutdown():
            rospy.sleep(0.05)

        # Inicializar servo
        self.portHandler = PortHandler(DEVICENAME)
        self.packetHandler = PacketHandler(PROTOCOL_VERSION)
        if not self.portHandler.openPort():
            raise RuntimeError(f"No se pudo abrir {DEVICENAME}")
        self.portHandler.setBaudRate(BAUDRATE)
        self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
        rospy.loginfo("✅ Servo conectado y torque habilitado.")

        # Parámetros configurables
        self.move_timeout_s = rospy.get_param("~servo_move_timeout", DEFAULT_MOVE_TIMEOUT)
        self.move_tolerance_ticks = rospy.get_param("~servo_tolerance_ticks", DEFAULT_MOVE_TOLERANCE_TICKS)

    def scan_callback(self, msg):
        self.latest_scan = msg

    def _read_present_position(self):
        """
        Lee ADDR_PRESENT_POSITION y devuelve el valor de ticks (int) o None.
        Maneja distintos formatos de retorno de la librería.
        """
        try:
            res = self.packetHandler.read2ByteTxRx(self.portHandler, DXL_ID, ADDR_PRESENT_POSITION)
            # Buscar primer int en la tupla/resultado
            if isinstance(res, (tuple, list)):
                for elem in res:
                    if isinstance(elem, int):
                        return elem
                try:
                    return int(res[0])
                except Exception:
                    return None
            if isinstance(res, int):
                return res
        except Exception as e:
            rospy.logwarn_throttle(5, f"No se pudo leer PRESENT_POSITION: {e}")
        return None

    def move_servo(self, pos_ticks):
        """
        Mueve el servo al goal y espera hasta que la lectura real esté dentro de tolerancia
        o hasta timeout. Devuelve la posición leída (int).
        """
        try:
            self.packetHandler.write2ByteTxRx(self.portHandler, DXL_ID, ADDR_GOAL_POSITION, int(pos_ticks))
        except Exception as e:
            rospy.logerr(f"Error enviando goal position: {e}")

        rospy.sleep(0.05)
        start = rospy.Time.now()
        timeout = rospy.Duration(self.move_timeout_s)
        last_present = None

        while not rospy.is_shutdown():
            present = self._read_present_position()
            if present is not None:
                last_present = present
                if abs(present - pos_ticks) <= self.move_tolerance_ticks:
                    return int(present)
            if rospy.Time.now() - start > timeout:
                rospy.logwarn(f"Timeout mover servo: objetivo={pos_ticks}, ultima_leida={last_present}")
                return int(last_present) if last_present is not None else int(pos_ticks)
            rospy.sleep(0.01)

        return int(last_present) if last_present is not None else int(pos_ticks)

    def get_scan_points(self, tilt_angle_rad):
        """
        Convierte el último LaserScan a Nx3 y aplica:
        p_world = R_x(tilt) * (p_lidar + OFFSET)
        - p_lidar está en el plano XY (Z=0)
        - OFFSET es vector desde el eje del servo hasta el centro del LIDAR (en m)
        """
        msg = self.latest_scan
        if msg is None:
            return np.empty((0,3))

        pts = []
        for i, r in enumerate(msg.ranges):
            if math.isnan(r) or r < self.min_range or r > self.max_range:
                continue
            angle = msg.angle_min + i * msg.angle_increment
            # limitar FOV si lo deseas (si fov < 360)
            if self.fov < 360.0 and abs(angle) > math.radians(self.fov/2.0):
                continue
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            z = 0.0
            pts.append([x, y, z])

        if not pts:
            return np.empty((0,3))

        pts = np.array(pts, dtype=float)

        # Añadir offset (trasladar cada punto al marco del eje del servo)
        pts_offset = pts + OFFSET  # (p_lidar + L)

        # Rotación alrededor de X (tilt_angle_rad) — eje de giro del servo es X
        c = math.cos(tilt_angle_rad)
        s = math.sin(tilt_angle_rad)
        R_x = np.array([
            [1.0, 0.0, 0.0],
            [0.0,   c,  -s],
            [0.0,   s,   c]
        ], dtype=float)

        pts_world = pts_offset @ R_x.T
        return pts_world

    def run_sweep(self):
        from datetime import datetime
        min_pos = TICKS_NEG90
        max_pos = TICKS_POS90
        delta = (max_pos - min_pos) / float(max(1, self.steps - 1))
        points_all = []

        # Crear carpeta de salida
        root_dir = rospy.get_param("~root_dir", "/home/p3at/capturas_lidar")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{self.prefix}_{timestamp}"
        out_dir = os.path.join(root_dir, folder_name)
        os.makedirs(out_dir, exist_ok=True)

        # Guardar calibración usada
        calib = {
            "ticks_neg90": int(TICKS_NEG90),
            "ticks_center": int(TICKS_CENTER),
            "ticks_pos90": int(TICKS_POS90),
            "offset_m": {"dx": float(DX), "dy": float(DY), "dz": float(DZ)}
        }
        with open(os.path.join(out_dir, "calibration.json"), "w") as f:
            json.dump(calib, f, indent=4)

        rospy.loginfo(f"📁 Carpeta creada: {out_dir}")

        rospy.loginfo("Moviendo servo al extremo inicial...")
        self.move_servo(int(min_pos))
        rospy.sleep(0.3)
        rospy.loginfo("Iniciando barrido...")

        for i in range(self.steps):
            pos_cmd = int(min_pos + i * delta)
            ticks_real = self.move_servo(pos_cmd)
            if ticks_real is None:
                rospy.logwarn(f"No se leyó posición real en paso {i}. Usando pos_cmd {pos_cmd}")
                ticks_real = pos_cmd

            ang_deg = ticks_to_angle(ticks_real)
            # NOTA: según convención, si al visualizar ves que el tilt es sentido contrario,
            # cambia la siguiente línea a: ang_rad = -math.radians(ang_deg)
            ang_rad = -math.radians(ang_deg)

            pts = self.get_scan_points(ang_rad)

            # Guardar slide
            slide_np = os.path.join(out_dir, f"slide_{i:03d}.npy")
            np.save(slide_np, pts)
            slide_meta = {
                "index": i,
                "servo_cmd_ticks": int(pos_cmd),
                "servo_present_ticks": int(ticks_real),
                "angle_deg": float(ang_deg),
                "angle_rad": float(ang_rad),
                "num_points": int(pts.shape[0]),
                "timestamp": rospy.Time.now().to_sec()
            }
            with open(os.path.join(out_dir, f"slide_{i:03d}.json"), "w") as f:
                json.dump(slide_meta, f, indent=4)

            if pts.size > 0:
                points_all.append(pts)
                self.slice_pub.publish(numpy_to_pointcloud2(pts))

            rospy.loginfo(f"Slide {i+1}/{self.steps} guardado: pts={pts.shape[0]} ticks_real={ticks_real} ang={ang_deg:.2f}°")

        # Guardar nube completa
        if points_all:
            cloud_np = np.vstack(points_all)
            cloud_path = os.path.join(out_dir, "cloud_full.npy")
            np.save(cloud_path, cloud_np)
            rospy.loginfo(f"✅ Nube completa guardada en: {cloud_path}")

            header = Header()
            header.stamp = rospy.Time.now()
            header.frame_id = "lidar_link"
            self.cloud_pub.publish(pc2.create_cloud_xyz32(header, cloud_np.tolist()))
            return cloud_path

        return ""

    def cleanup(self):
        try:
            self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        except Exception as e:
            rospy.logwarn(f"Error deshabilitando torque: {e}")
        try:
            self.portHandler.closePort()
        except Exception:
            pass
        rospy.loginfo("✅ Servo deshabilitado y puerto cerrado.")

def handle_lidar_sweep(req):
    try:
        scanner = LidarServoScanner(steps=req.steps,
                                    min_range=req.min_range,
                                    max_range=req.max_range,
                                    fov=req.fov,
                                    prefix=req.prefix)
        cloud_path = scanner.run_sweep()
        scanner.cleanup()
        if cloud_path:
            return LidarSweepResponse(cloud_path=cloud_path, success=True, message="Barrido completado")
        else:
            return LidarSweepResponse(cloud_path="", success=False, message="Ningún punto capturado")
    except Exception as e:
        rospy.logerr(f"Error barrido: {e}")
        return LidarSweepResponse(cloud_path="", success=False, message=str(e))

def lidar_service_node():
    rospy.init_node("lidar_servo_service_node")
    rospy.Service('/lidar_sweep', LidarSweep, handle_lidar_sweep)
    rospy.loginfo("🚀 Servicio /lidar_sweep listo")
    rospy.spin()

if __name__ == "__main__":
    lidar_service_node()
