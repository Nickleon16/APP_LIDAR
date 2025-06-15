import open3d as o3d
import urllib.request
import tempfile

# URL de una nube de puntos en formato PCD (del repositorio de PCL)
url = "https://raw.githubusercontent.com/PointCloudLibrary/data/master/tutorials/table_scene_lms400.pcd"

with tempfile.NamedTemporaryFile(suffix=".pcd", delete=False) as f:
    print(f"Descargando {url} ...")
    urllib.request.urlretrieve(url, f.name)
    nube = o3d.io.read_point_cloud(f.name)
    print("Número de puntos:", len(nube.points))
    o3d.visualization.draw_geometries([nube])
