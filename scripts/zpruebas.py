import open3d as o3d

pcd = o3d.io.read_point_cloud("recursos/mesa.pcd")
resto = pcd  # copia inicial

planes = []
colors = [[1, 0, 1], [0, 1, 0], [0, 0, 1]]  # colores para planos

for i in range(3): 
    plane_model, inliers = resto.segment_plane(
        distance_threshold=0.01,
        ransac_n=3,
        num_iterations=1000
    )

    inlier_cloud = resto.select_by_index(inliers)
    inlier_cloud.paint_uniform_color(colors[i % len(colors)])
    planes.append(inlier_cloud)

    # Quitar plano segmentado
    resto = resto.select_by_index(inliers, invert=True)

# Visualizar los planos encontrados + lo que queda
#o3d.visualization.draw_geometries(planes + [resto])
o3d.visualization.draw_geometries(planes)
