#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import math
import json
import argparse
import numpy as np
import open3d as o3d
import rospy
from sensor_msgs.msg import LaserScan
from dynamixel_sdk import *  # SDK del servo

# ==== CONFIGURACIÓN SERVO ====
DEVICENAME = '/dev/ttyUSB0'
BAUDRATE = 57600
PROTOCOL_VERSION = 1.0
DXL_ID = 1

ADDR_TORQUE_ENABLE     = 24
ADDR_GOAL_POSITION     = 30
ADDR_PRESENT_POSITION  = 36
TORQUE_ENABLE          = 1
TORQUE_DISABLE         = 0

# ==== CALIBRACIÓN ====
DXL_POS_NEG90 = 2500   # -90°
DXL_POS_POS90 = 500    # +90°
DXL_POS_CENTER = (DXL_POS_NEG90 + DXL_POS_POS90) // 2  # ~1500 → 0°

DEG_PER_TICK = 180.0 / (DXL_POS_NEG90 - DXL_POS_POS90)  # 180° entre ticks


class LidarServoScanner:
    def __init__(self):
        parser = argparse.ArgumentParser(description="Captura nube 3D con servo y LIDAR")
        parser.add_argument("--min_range", type=float, default=0.05)
        parser.add_argument("--max_range", type=float, default=5.0)
        parser.add_argument("--steps", type=int, default=40)
        parser.add_argument("--fov", type=float, default=30.0)
        parser.add_argument("--prefix", type=str, default="barrido")
        self.args = parser.parse_args()

        print(f"📋 Configuración: steps={self.args.steps}, rango=[{self.args.min_range}, {self.args.max_range}], FOV={self.args.fov}")

        # ROS init
        rospy.init_node("lidar_servo_barrido", anonymous=True)
        rospy.Subscriber("/scan", LaserScan, self.scan_callback)
        self.latest_scan = None
        self.points_all = []

        while self.latest_scan is None and not rospy.is_shutdown():
            rospy.sleep(0.05)

        # Servo init
        self.portHandler = PortHandler(DEVICENAME)
        self.packetHandler = PacketHandler(PROTOCOL_VERSION)
        if not self.portHandler.openPort():
            raise RuntimeError("❌ No se pudo abrir el puerto del servo.")
        self.portHandler.setBaudRate(BAUDRATE)
        self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
        print("✅ Servo conectado y torque habilitado.")

    # -------------------------------------
    def scan_callback(self, msg):
        self.latest_scan = msg

    # -------------------------------------
    def move_servo(self, pos_ticks):
        self.packetHandler.write2ByteTxRx(self.portHandler, DXL_ID, ADDR_GOAL_POSITION, int(pos_ticks))
        rospy.sleep(0.1)

    # -------------------------------------
    def get_scan_points(self, tilt_angle_rad):
        msg = self.latest_scan
        if msg is None:
            return np.empty((0, 3))

        pts = []
        for i, r in enumerate(msg.ranges):
            if math.isnan(r) or r < self.args.min_range or r > self.args.max_range:
                continue
            angle = msg.angle_min + i * msg.angle_increment
            if abs(angle) > math.radians(self.args.fov):
                continue
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            z = 0.0
            pts.append([x, y, z])

        if not pts:
            return np.empty((0, 3))

        # Rotar en eje X según el ángulo de barrido
        R_x = np.array([
            [1, 0, 0],
            [0, math.cos(tilt_angle_rad), -math.sin(tilt_angle_rad)],
            [0, math.sin(tilt_angle_rad),  math.cos(tilt_angle_rad)]
        ])
        pts = np.array(pts) @ R_x.T
        return pts, R_x

    # -------------------------------------
    def run_sweep(self):
        steps = int(self.args.steps)
        min_pos = DXL_POS_NEG90
        max_pos = DXL_POS_POS90
        delta = (max_pos - min_pos) / float(steps - 1)
        self.points_all.clear()

        # Carpeta de salida
        out_dir = self.args.prefix
        os.makedirs(out_dir, exist_ok=True)
        metadata = {
            "prefix": self.args.prefix,
            "steps": steps,
            "min_range": self.args.min_range,
            "max_range": self.args.max_range,
            "fov": self.args.fov,
            "captures": []
        }

        print(f"🎯 Barrido de -90° a +90° con {steps} pasos")

        for i in range(steps):
            pos = int(min_pos + i * delta)
            self.move_servo(pos)

            if i == 0:
                rospy.sleep(1.0)
            else:
                rospy.sleep(0.1)

            ang_deg = (pos - DXL_POS_CENTER) * DEG_PER_TICK
            ang_rad = math.radians(ang_deg)
            print(f"📸 Captura {i+1}/{steps} | Servo:{pos} | Ángulo:{ang_deg:.2f}°")

            pts, R_x = self.get_scan_points(ang_rad)
            if pts.shape[0] > 0:
                self.points_all.append(pts)

                # Guardar puntos individuales
                filename = f"capture_{i:03d}.npy"
                np.save(os.path.join(out_dir, filename), pts)

                # Guardar metadatos con matriz de rotación
                metadata["captures"].append({
                    "index": i,
                    "servo_pos": pos,
                    "angle_deg": ang_deg,
                    "angle_rad": ang_rad,
                    "file": filename,
                    "num_points": int(pts.shape[0]),
                    "rotation_matrix": R_x.tolist()
                })

        if not self.points_all:
            print("⚠️ No se obtuvieron puntos válidos.")
            return

        # Guardar nube completa
        cloud_np = np.vstack(self.points_all)
        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(cloud_np)
        temp_cloud_path = "temp_cloud.pcd"
        o3d.io.write_point_cloud(temp_cloud_path, cloud)
        print(f"💾 Nube temporal guardada: {temp_cloud_path} ({len(cloud.points)} puntos)")

        # Guardar metadatos
        meta_path = os.path.join(out_dir, "sweep_metadata.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"🗂️ Metadatos guardados en: {meta_path}")

    # -------------------------------------
    def cleanup(self):
        self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        self.portHandler.closePort()
        print("✅ Servo deshabilitado y puerto cerrado.")

    # -------------------------------------
    def run(self):
        try:
            self.run_sweep()
        finally:
            self.cleanup()


if __name__ == "__main__":
    scanner = LidarServoScanner()
    scanner.run()
