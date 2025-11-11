#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import math
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

# ==== CALIBRACIÓN ====
DXL_POS_NEG90 = 2500
DXL_POS_POS90 = 500
DXL_POS_CENTER = (DXL_POS_NEG90 + DXL_POS_POS90) // 2
DEG_PER_TICK = 180.0 / (DXL_POS_NEG90 - DXL_POS_POS90)


def numpy_to_pointcloud2(points, frame_id="lidar_link"):
    fields = [
        PointField('x', 0, PointField.FLOAT32, 1),
        PointField('y', 4, PointField.FLOAT32, 1),
        PointField('z', 8, PointField.FLOAT32, 1)
    ]
    header = Header()
    header.stamp = rospy.Time.now()
    header.frame_id = frame_id
    ### FIX: Convertir a lista
    return pc2.create_cloud(header, fields, points.tolist())


class LidarServoScanner:
    def __init__(self, steps=10, min_range=0.05, max_range=5.0, fov=30.0, prefix="barrido"):
        self.steps = steps
        self.min_range = min_range
        self.max_range = max_range
        self.fov = fov
        self.prefix = prefix

        self.latest_scan = None
        self.points_all = []

        # No volver a inicializar ROS aquí
        ### FIX: Quitar init_node
        rospy.Subscriber("/scan", LaserScan, self.scan_callback)
        self.slice_pub = rospy.Publisher("/lidar_slice", PointCloud2, queue_size=1)
        self.cloud_pub = rospy.Publisher("/lidar_cloud", PointCloud2, queue_size=1)


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

    def scan_callback(self, msg):
        self.latest_scan = msg

    def move_servo(self, pos_ticks):
        self.packetHandler.write2ByteTxRx(self.portHandler, DXL_ID, ADDR_GOAL_POSITION, int(pos_ticks))
        rospy.sleep(0.1)

    def get_scan_points(self, tilt_angle_rad):
        msg = self.latest_scan
        if msg is None:
            return np.empty((0, 3))
        pts = []
        for i, r in enumerate(msg.ranges):
            if math.isnan(r) or r < self.min_range or r > self.max_range:
                continue
            angle = msg.angle_min + i * msg.angle_increment
            if abs(angle) > math.radians(self.fov):
                continue
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            z = 0.0
            pts.append([x, y, z])
        if not pts:
            return np.empty((0, 3))
        R_x = np.array([
            [1, 0, 0],
            [0, math.cos(tilt_angle_rad), -math.sin(tilt_angle_rad)],
            [0, math.sin(tilt_angle_rad), math.cos(tilt_angle_rad)]
        ])
        return np.array(pts) @ R_x.T

    def run_sweep(self):
        min_pos = DXL_POS_NEG90
        max_pos = DXL_POS_POS90
        delta = (max_pos - min_pos) / float(self.steps - 1)
        points_all = []

        out_dir = rospy.get_param("~out_dir", "/tmp")
        os.makedirs(out_dir, exist_ok=True)

        rospy.loginfo("Moviendo servo a -90° para iniciar barrido...")
        self.move_servo(min_pos)
        rospy.sleep(0.8)  ### FIX: delay más razonable
        rospy.loginfo("Servo listo. Iniciando barrido...")

        for i in range(self.steps):
            pos = int(min_pos + i * delta)
            self.move_servo(pos)

            ang_deg = (pos - DXL_POS_CENTER) * DEG_PER_TICK
            ang_rad = math.radians(ang_deg)

            pts = self.get_scan_points(ang_rad)

            if pts.size > 0:
                points_all.append(pts)                
                self.slice_pub.publish(numpy_to_pointcloud2(pts))
            rospy.loginfo(f"Barrido {i+1}/{self.steps} publicado ({pts.shape[0] if pts.size>0 else 0} puntos)")

        if points_all:
            cloud_np = np.vstack(points_all)
            cloud_path = os.path.join(out_dir, f"{self.steps}_points.npy")
            np.save(cloud_path, cloud_np)
            rospy.loginfo(f"✅ Nube guardada en: {cloud_path}")

            header = Header()
            header.stamp = rospy.Time.now()
            header.frame_id = "lidar_link"
            self.cloud_pub.publish(pc2.create_cloud_xyz32(header, cloud_np.tolist()))

            return cloud_path

        return ""

    def cleanup(self):
        self.packetHandler.write1ByteTxRx(self.portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        self.portHandler.closePort()
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
