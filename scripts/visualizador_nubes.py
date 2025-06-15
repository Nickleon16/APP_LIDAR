# visualizador_nubes.py

import sys
import open3d as o3d
import os

path = sys.argv[1]
nube = o3d.io.read_point_cloud(path)    
o3d.visualization.draw_geometries([nube])
os.remove(path)  # limpia después de mostrar