"""
LiDAR Infrastructure Inspector - Point Cloud Registration
ICP (Iterative Closest Point) alignment with progress tracking
"""
import numpy as np
import open3d as o3d
from typing import Tuple, Optional, Callable, Dict, List


class RegistrationResult:
    """Container for registration results and metrics"""
    
    def __init__(self, transformation: np.ndarray, fitness: float, 
                 inlier_rmse: float, correspondence_set: np.ndarray,
                 iteration_log: List[Dict] = None):
        self.transformation = transformation
        self.fitness = fitness
        self.inlier_rmse = inlier_rmse
        self.correspondence_set = correspondence_set
        self.iteration_log = iteration_log or []
    
    def __repr__(self):
        return (f"RegistrationResult(fitness={self.fitness:.4f}, "
                f"inlier_rmse={self.inlier_rmse:.4f}, "
                f"iterations={len(self.iteration_log)})")


def align_point_clouds_icp(
    source: o3d.geometry.PointCloud,
    target: o3d.geometry.PointCloud,
    max_correspondence_distance: float = 0.5,
    max_iterations: int = 50,
    relative_fitness: float = 1e-6,
    relative_rmse: float = 1e-6,
    progress_callback: Optional[Callable[[int, float], None]] = None
) -> RegistrationResult:
    """
    Align source point cloud to target using ICP.
    
    Args:
        source: Source point cloud (will be transformed)
        target: Target point cloud (reference)
        max_correspondence_distance: Maximum distance for point correspondences
        max_iterations: Maximum number of ICP iterations
        relative_fitness: Convergence criterion for fitness
        relative_rmse: Convergence criterion for RMSE
        progress_callback: Optional callback(iteration, rmse) for progress updates
        
    Returns:
        RegistrationResult with transformation matrix and metrics
    """
    # Ensure point clouds have normals for better alignment
    if not source.has_normals():
        source.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )
    
    if not target.has_normals():
        target.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )
    
    # Initial alignment using point-to-plane ICP
    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(
        relative_fitness=relative_fitness,
        relative_rmse=relative_rmse,
        max_iteration=max_iterations
    )
    
    # Track iterations for convergence plot
    iteration_log = []
    
    # Custom callback wrapper to track progress
    class IterationCallback:
        def __init__(self):
            self.iteration = 0
            
        def __call__(self, iteration_result):
            self.iteration += 1
            rmse = iteration_result.inlier_rmse
            fitness = iteration_result.fitness
            
            iteration_log.append({
                'iteration': self.iteration,
                'rmse': rmse,
                'fitness': fitness
            })
            
            if progress_callback:
                progress_callback(self.iteration, rmse)
            
            return True  # Continue iterations
    
    callback = IterationCallback()
    
    # Run point-to-plane ICP
    reg_result = o3d.pipelines.registration.registration_icp(
        source, target,
        max_correspondence_distance,
        np.eye(4),  # Initial transformation (identity)
        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
        criteria
    )
    
    # Create our result object
    result = RegistrationResult(
        transformation=reg_result.transformation,
        fitness=reg_result.fitness,
        inlier_rmse=reg_result.inlier_rmse,
        correspondence_set=np.asarray(reg_result.correspondence_set),
        iteration_log=iteration_log
    )
    
    return result


def apply_transformation(
    pcd: o3d.geometry.PointCloud,
    transformation: np.ndarray
) -> o3d.geometry.PointCloud:
    """
    Apply transformation matrix to point cloud.
    
    Args:
        pcd: Input point cloud
        transformation: 4x4 transformation matrix
        
    Returns:
        Transformed point cloud (new copy)
    """
    pcd_transformed = o3d.geometry.PointCloud(pcd)
    pcd_transformed.transform(transformation)
    return pcd_transformed


def estimate_initial_alignment(
    source: o3d.geometry.PointCloud,
    target: o3d.geometry.PointCloud,
    voxel_size: float = 0.05
) -> np.ndarray:
    """
    Estimate initial rough alignment using FPFH features and RANSAC.
    Useful for clouds that are far apart.
    
    Args:
        source: Source point cloud
        target: Target point cloud
        voxel_size: Voxel size for downsampling
        
    Returns:
        4x4 transformation matrix
    """
    # Downsample
    source_down = source.voxel_down_sample(voxel_size)
    target_down = target.voxel_down_sample(voxel_size)
    
    # Estimate normals
    radius_normal = voxel_size * 2
    source_down.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30)
    )
    target_down.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_normal, max_nn=30)
    )
    
    # Compute FPFH features
    radius_feature = voxel_size * 5
    source_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        source_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100)
    )
    target_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        target_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=radius_feature, max_nn=100)
    )
    
    # RANSAC registration
    distance_threshold = voxel_size * 1.5
    result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
        source_down, target_down,
        source_fpfh, target_fpfh,
        mutual_filter=True,
        max_correspondence_distance=distance_threshold,
        estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
        ransac_n=4,
        checkers=[
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(distance_threshold)
        ],
        criteria=o3d.pipelines.registration.RANSACConvergenceCriteria(4000000, 500)
    )
    
    return result.transformation


def get_alignment_quality_description(fitness: float, rmse: float) -> str:
    """
    Get human-readable description of alignment quality.
    
    Args:
        fitness: Fitness score (0-1, higher is better)
        rmse: Root mean square error
        
    Returns:
        Quality description string
    """
    if fitness > 0.8:
        quality = "Excellent"
    elif fitness > 0.6:
        quality = "Good"
    elif fitness > 0.4:
        quality = "Fair"
    elif fitness > 0.2:
        quality = "Poor"
    else:
        quality = "Very Poor"
    
    return f"{quality} (fitness: {fitness:.3f}, RMSE: {rmse:.4f}m)"
