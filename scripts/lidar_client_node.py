#!/usr/bin/env python3
import rospy
from APP_LIDAR.srv import LidarSweep
from sensor_msgs.msg import PointCloud2
import sensor_msgs.point_cloud2 as pc2
import numpy as np
import open3d as o3d

class LidarClient:
    def __init__(self):
        rospy.init_node("lidar_client_node")
        self.points = []

        # Suscripción al tópico de nube del robot
        rospy.Subscriber("/lidar_points", PointCloud2, self.pc_callback)

        # Espera que el servicio esté disponible
        rospy.wait_for_service('/lidar_sweep')
        self.lidar_sweep_srv = rospy.ServiceProxy('/lidar_sweep', LidarSweep)
        rospy.loginfo("Cliente listo para llamar al servicio /lidar_sweep")

    def pc_callback(self, msg):
        # Convierte PointCloud2 a numpy
        pts = np.array(list(pc2.read_points(msg, field_names=("x","y","z"))))
        if pts.size > 0:
            self.points.append(pts)

    def do_sweep(self, steps=16, min_range=0.1, max_range=8.0, fov=45.0, prefix="hardware_nube"):
        try:
            rospy.loginfo("📡 Llamando al servicio /lidar_sweep...")
            resp = self.lidar_sweep_srv(steps, min_range, max_range, fov, prefix)
            if not resp.success:
                rospy.logwarn(f"⚠️ Sweep fallido: {resp.message}")
                return

            rospy.loginfo(f"✅ Sweep completado, nube guardada en robot: {resp.cloud_path}")
            
            # Espera que lleguen todos los puntos
            rospy.sleep(1.0)

            if not self.points:
                rospy.logwarn("⚠️ No se recibieron puntos del robot")
                return

            # Unir todos los puntos en un array
            cloud_np = np.vstack(self.points)
            rospy.loginfo(f"Nube recibida con {cloud_np.shape[0]} puntos")

            # Mostrar con Open3D
            cloud = o3d.geometry.PointCloud()
            cloud.points = o3d.utility.Vector3dVector(cloud_np)
            o3d.visualization.draw_geometries([cloud], window_name="Nube LIDAR")

        except rospy.ServiceException as e:
            rospy.logerr(f"Error llamando al servicio: {e}")

if __name__ == "__main__":
    client = LidarClient()
    client.do_sweep(steps=60, min_range=0.1, max_range=8.0, fov=45.0, prefix="hardware_nube")
    rospy.spin()
