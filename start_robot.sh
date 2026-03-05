#!/bin/bash

roscore &
sleep 3
rosrun rosaria RosAria &
sleep 3
rosrun hokuyo_node hokuyo_node _port:=/dev/ttyACM0 &
sleep 3
python3 ~/catkin_ws/src/APP_LIDAR/scripts/lidar_servo_service_node.py