import open3d as o3d
import numpy as np
import copy
import yaml


# ----------------- CARGA DE CONFIGURACIÓN -----------------
def load_yaml_config(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


# ----------------- PREPROCESAMIENTO -----------------
def preprocess_point_cloud(pcd, voxel_size, cfg):
    # Downsample
    pcd_down = pcd.voxel_down_sample(voxel_size)

    # Filtrar por altura (Z)
    z_min, z_max = cfg["z_min"], cfg["z_max"]
    points = np.asarray(pcd_down.points)
    mask = (points[:, 2] >= z_min) & (points[:, 2] <= z_max)
    pcd_down.points = o3d.utility.Vector3dVector(points[mask])

    # Estimación de normales
    pcd_down.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(
            radius=cfg["normal_radius"],
            max_nn=cfg["normal_max_nn"]
        )
    )
    pcd_down.orient_normals_consistent_tangent_plane(cfg["consistent_orientation_k"])
    pcd_down.orient_normals_towards_camera_location(camera_location=[0, 0, 0])

    # Calcular FPFH
    fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(
            radius=voxel_size * cfg["fpfh_radius_multiplier"],
            max_nn=cfg["fpfh_max_nn"]
        )
    )
    return pcd_down, fpfh


# ----------------- RANSAC CON FPFH -----------------
def execute_global_registration(source_down, target_down, source_fpfh, target_fpfh, voxel_size, cfg):
    distance_threshold = voxel_size * cfg["distance_threshold_multiplier"]

    # Tipo de estimación
    estimation_method = (
        o3d.pipelines.registration.TransformationEstimationPointToPlane()
        if cfg["estimation_method"] == "point_to_plane"
        else o3d.pipelines.registration.TransformationEstimationPointToPoint(False)
    )

    result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
        source_down, target_down,
        source_fpfh, target_fpfh,
        mutual_filter=cfg["mutual_filter"],
        max_correspondence_distance=distance_threshold,
        estimation_method=estimation_method,
        ransac_n=cfg["ransac_n"],
        checkers=[
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(cfg["checker_edge_length"]),
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(distance_threshold)
        ],
        criteria=o3d.pipelines.registration.RANSACConvergenceCriteria(
            cfg["criteria_max_iterations"],
            cfg["criteria_confidence"]
        )
    )
    return result


# ----------------- ICP REFINADO -----------------
def refine_registration(source, target, initial_transformation, voxel_size, cfg):
    distance_threshold = voxel_size * cfg["distance_threshold_multiplier"]

    estimation_method = (
        o3d.pipelines.registration.TransformationEstimationPointToPlane()
        if cfg["estimation_method"] == "point_to_plane"
        else o3d.pipelines.registration.TransformationEstimationPointToPoint(False)
    )

    result = o3d.pipelines.registration.registration_icp(
        source, target,
        max_correspondence_distance=distance_threshold,
        init=initial_transformation,
        estimation_method=estimation_method
    )
    return result


# ----------------- REGISTRO MÚLTIPLE -----------------
def register_point_clouds(pcd_list, voxel_size, preprocess_cfg, ransac_cfg, icp_cfg):
    assert len(pcd_list) > 1, "Se necesitan al menos dos nubes"

    accumulated = copy.deepcopy(pcd_list[0])

    for i in range(1, len(pcd_list)):
        source = pcd_list[i]
        target = accumulated

        # Preprocesamiento
        source_down, source_fpfh = preprocess_point_cloud(source, voxel_size, preprocess_cfg)
        target_down, target_fpfh = preprocess_point_cloud(target, voxel_size, preprocess_cfg)

        # RANSAC
        result_ransac = execute_global_registration(source_down, target_down, source_fpfh, target_fpfh, voxel_size, ransac_cfg)
        print(f"\n[ RANSAC | Nube {i+1} ]")
        print(f"  Fitness: {result_ransac.fitness:.4f}")
        print(f"  Inlier RMSE: {result_ransac.inlier_rmse:.6f}")

        # Normales para ICP
        source_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(
            radius=voxel_size * icp_cfg["normal_radius_multiplier"],
            max_nn=icp_cfg["normal_max_nn"]
        ))
        target_down.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(
            radius=voxel_size * icp_cfg["normal_radius_multiplier"],
            max_nn=icp_cfg["normal_max_nn"]
        ))

        # ICP
        result_icp = refine_registration(source_down, target_down, result_ransac.transformation, voxel_size, icp_cfg)
        print(f"[ ICP | Nube {i+1} ]")
        print(f"  Fitness: {result_icp.fitness:.4f}")
        print(f"  Inlier RMSE: {result_icp.inlier_rmse:.6f}")

        # Aplicar transformación y acumular
        source_down.transform(result_icp.transformation)
        accumulated += source_down

        print(f"Nube {i+1}/{len(pcd_list)} registrada correctamente")

    return accumulated


# ----------------- MAIN -----------------
if __name__ == "__main__":
    # Cargar configuraciones
    preprocess_cfg = load_yaml_config("preprocess.yaml")["preprocess"]
    ransac_cfg = load_yaml_config("ransac.yaml")["ransac"]
    icp_cfg = load_yaml_config("icp.yaml")["icp"]
    general_cfg = load_yaml_config("general.yaml")["general"]

    voxel_size = preprocess_cfg["voxel_size"]
    files = general_cfg["input_files"]

    print("Archivos a registrar:")
    for f in files:
        print("  -", f)

    pcd_list = [o3d.io.read_point_cloud(f) for f in files]

    print("\nIniciando registro múltiple...\n")

    result = register_point_clouds(pcd_list, voxel_size, preprocess_cfg, ransac_cfg, icp_cfg)

    print("\nRegistro completo. Guardando resultados...")

    o3d.io.write_point_cloud(general_cfg["output_file"], result)
    print(f"Resultado guardado en: {general_cfg['output_file']}")

    # Visualización
    o3d.visualization.draw_geometries([result], window_name=general_cfg["visualization_window_name"])
