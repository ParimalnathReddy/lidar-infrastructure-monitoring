"""
LiDAR Infrastructure Inspector - Point Cloud Segmentation
Ground plane removal using RANSAC
"""
import numpy as np
import open3d as o3d
from typing import Tuple, Optional


class SegmentationResult:
    """Container for segmentation results"""
    
    def __init__(self, inliers: np.ndarray, outliers: np.ndarray,
                 plane_model: np.ndarray, num_inliers: int):
        self.inliers = inliers  # Indices of ground points
        self.outliers = outliers  # Indices of non-ground points
        self.plane_model = plane_model  # [a, b, c, d] for ax + by + cz + d = 0
        self.num_inliers = num_inliers
    
    def get_plane_equation_str(self) -> str:
        """Get human-readable plane equation"""
        a, b, c, d = self.plane_model
        return f"{a:.3f}x + {b:.3f}y + {c:.3f}z + {d:.3f} = 0"
    
    def __repr__(self):
        return (f"SegmentationResult(inliers={self.num_inliers}, "
                f"outliers={len(self.outliers)})")


def remove_ground_plane(
    pcd: o3d.geometry.PointCloud,
    distance_threshold: float = 0.2,
    ransac_n: int = 3,
    num_iterations: int = 1000
) -> Tuple[o3d.geometry.PointCloud, o3d.geometry.PointCloud, SegmentationResult]:
    """
    Remove ground plane from point cloud using RANSAC.
    
    Args:
        pcd: Input point cloud
        distance_threshold: Maximum distance from plane to be considered inlier (meters)
        ransac_n: Number of points to sample for RANSAC
        num_iterations: Number of RANSAC iterations
        
    Returns:
        Tuple of (ground_cloud, non_ground_cloud, segmentation_result)
    """
    # Segment plane using RANSAC
    plane_model, inliers = pcd.segment_plane(
        distance_threshold=distance_threshold,
        ransac_n=ransac_n,
        num_iterations=num_iterations
    )
    
    # Create result object
    all_indices = np.arange(len(pcd.points))
    outliers = np.setdiff1d(all_indices, inliers)
    
    result = SegmentationResult(
        inliers=np.asarray(inliers),
        outliers=outliers,
        plane_model=np.asarray(plane_model),
        num_inliers=len(inliers)
    )
    
    # Extract ground and non-ground clouds
    ground_cloud = pcd.select_by_index(inliers)
    non_ground_cloud = pcd.select_by_index(inliers, invert=True)
    
    # Color ground points (optional, for visualization)
    ground_cloud.paint_uniform_color([0.5, 0.5, 0.5])  # Gray
    
    return ground_cloud, non_ground_cloud, result


def remove_statistical_outliers(
    pcd: o3d.geometry.PointCloud,
    nb_neighbors: int = 20,
    std_ratio: float = 2.0
) -> Tuple[o3d.geometry.PointCloud, o3d.geometry.PointCloud]:
    """
    Remove statistical outliers from point cloud.
    
    Args:
        pcd: Input point cloud
        nb_neighbors: Number of neighbors to analyze
        std_ratio: Standard deviation ratio threshold
        
    Returns:
        Tuple of (inlier_cloud, outlier_cloud)
    """
    cl, ind = pcd.remove_statistical_outlier(
        nb_neighbors=nb_neighbors,
        std_ratio=std_ratio
    )
    
    inlier_cloud = pcd.select_by_index(ind)
    outlier_cloud = pcd.select_by_index(ind, invert=True)
    
    return inlier_cloud, outlier_cloud


def downsample_voxel(
    pcd: o3d.geometry.PointCloud,
    voxel_size: float = 0.05
) -> o3d.geometry.PointCloud:
    """
    Downsample point cloud using voxel grid.
    
    Args:
        pcd: Input point cloud
        voxel_size: Size of voxel grid
        
    Returns:
        Downsampled point cloud
    """
    return pcd.voxel_down_sample(voxel_size=voxel_size)


def estimate_normals(
    pcd: o3d.geometry.PointCloud,
    radius: float = 0.1,
    max_nn: int = 30
) -> o3d.geometry.PointCloud:
    """
    Estimate normals for point cloud.
    
    Args:
        pcd: Input point cloud
        radius: Search radius for normal estimation
        max_nn: Maximum number of neighbors
        
    Returns:
        Point cloud with normals (modifies in place and returns)
    """
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(
            radius=radius,
            max_nn=max_nn
        )
    )
    return pcd


def cluster_dbscan(
    pcd: o3d.geometry.PointCloud,
    eps: float = 0.5,
    min_points: int = 10
) -> Tuple[np.ndarray, int]:
    """
    Cluster point cloud using DBSCAN.
    
    Args:
        pcd: Input point cloud
        eps: Maximum distance between points in a cluster
        min_points: Minimum number of points to form a cluster
        
    Returns:
        Tuple of (labels array, number of clusters)
        Labels: -1 for noise, 0+ for cluster ID
    """
    labels = np.array(pcd.cluster_dbscan(
        eps=eps,
        min_points=min_points,
        print_progress=False
    ))
    
    num_clusters = labels.max() + 1
    
    return labels, num_clusters


def get_ground_removal_stats(result: SegmentationResult, 
                             original_count: int) -> str:
    """
    Get human-readable statistics for ground removal.
    
    Args:
        result: Segmentation result
        original_count: Original point count
        
    Returns:
        Statistics string
    """
    ground_pct = (result.num_inliers / original_count) * 100
    remaining_pct = 100 - ground_pct
    
    stats = [
        f"Ground points: {result.num_inliers:,} ({ground_pct:.1f}%)",
        f"Remaining: {len(result.outliers):,} ({remaining_pct:.1f}%)",
        f"Plane: {result.get_plane_equation_str()}"
    ]
    
    return " | ".join(stats)
