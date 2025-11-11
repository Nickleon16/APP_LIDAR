#!/usr/bin/env python3
import rospy
import requests
import json
from sensor_msgs.msg import LaserScan
import math

API_URL = "http://192.168.3.188:5000/api/nube_robot"  # <-- IP y endpoint en laptop

def scan_callback(msg):
    # Convertimos LaserScan a puntos (x, y)
    angles = [msg.angle_min + i * msg.angle_increment for i in range(len(msg.ranges))]
    points = []

    for r, a in zip(msg.ranges, angles):
        if math.isfinite(r):
            x = r * math.cos(a)
            y = r * math.sin(a)
            points.append([x, y])

    # Enviar datos al API como JSON
    try:
        payload = {
            "robot_id": "p3at_001",
            "points": points
        }
        requests.post(API_URL, json=payload, timeout=0.5)
    except Exception as e:
        rospy.logwarn(f"Error enviando nube: {e}")

def main():
    rospy.init_node("robot_lidar_sender")
    rospy.Subscriber("/scan", LaserScan, scan_callback)
    rospy.spin()

if __name__ == "__main__":
    main()
