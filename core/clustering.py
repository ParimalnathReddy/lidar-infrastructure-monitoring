"""
LiDAR Infrastructure Inspector - Point Cloud Clustering
DBSCAN clustering with utilities for defect detection
"""
import numpy as np
import open3d as o3d
from typing import Tuple, List, Dict, Optional
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


class ClusterInfo:
    """Container for cluster information"""
    
    def __init__(self, cluster_id: int, indices: np.ndarray, points: np.ndarray):
        self.cluster_id = cluster_id
        self.indices = indices
        self.points = points
        self.num_points = len(indices)
        
        # Compute bounding box
        self.bbox_min = points.min(axis=0)
        self.bbox_max = points.max(axis=0)
        self.bbox_size = self.bbox_max - self.bbox_min
        
        # Compute volume (bbox volume as proxy)
        self.volume = np.prod(self.bbox_size)
        
        # Compute centroid
        self.centroid = points.mean(axis=0)
    
    def __repr__(self):
        return (f"Cluster {self.cluster_id}: {self.num_points} points, "
                f"volume={self.volume:.3f}m³")


class ClusteringResult:
    """Container for clustering results"""
    
    def __init__(self, labels: np.ndarray, eps: float, min_samples: int):
        self.labels = labels
        self.eps = eps
        self.min_samples = min_samples
        
        # Compute statistics
        self.num_clusters = labels.max() + 1 if len(labels) > 0 else 0
        self.num_noise = np.sum(labels == -1)
        self.num_clustered = len(labels) - self.num_noise
        
        # Cluster sizes
        self.cluster_sizes = {}
        for i in range(self.num_clusters):
            self.cluster_sizes[i] = np.sum(labels == i)
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        if self.num_clusters == 0:
            return "No clusters found"
        
        return (f"{self.num_clusters} clusters | "
                f"{self.num_clustered:,} points clustered | "
                f"{self.num_noise:,} noise points")
    
    def __repr__(self):
        return f"ClusteringResult({self.get_summary()})"


def cluster_dbscan(
    pcd: o3d.geometry.PointCloud,
    eps: float = 0.5,
    min_samples: int = 10,
    filter_by_distance: bool = False,
    distance_threshold: float = 0.1,
    distances: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, ClusteringResult]:
    """
    Cluster point cloud using DBSCAN.
    
    Args:
        pcd: Input point cloud
        eps: Maximum distance between points in a cluster
        min_samples: Minimum number of points to form a cluster
        filter_by_distance: If True, only cluster points above distance threshold
        distance_threshold: Threshold for filtering (if filter_by_distance=True)
        distances: Distance array for filtering (required if filter_by_distance=True)
        
    Returns:
        Tuple of (labels array, ClusteringResult)
        Labels: -1 for noise, 0+ for cluster ID
    """
    points = np.asarray(pcd.points)
    
    # Filter points if requested
    if filter_by_distance and distances is not None:
        mask = np.abs(distances) > distance_threshold
        points_to_cluster = points[mask]
        original_indices = np.where(mask)[0]
    else:
        points_to_cluster = points
        original_indices = np.arange(len(points))
    
    # Run DBSCAN
    if len(points_to_cluster) > 0:
        clustering = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)
        cluster_labels = clustering.fit_predict(points_to_cluster)
        
        # Map back to original indices
        labels = np.full(len(points), -1, dtype=int)
        labels[original_indices] = cluster_labels
    else:
        labels = np.full(len(points), -1, dtype=int)
    
    result = ClusteringResult(labels, eps, min_samples)
    
    return labels, result


def extract_cluster_info(
    pcd: o3d.geometry.PointCloud,
    labels: np.ndarray
) -> List[ClusterInfo]:
    """
    Extract information for each cluster.
    
    Args:
        pcd: Point cloud
        labels: Cluster labels
        
    Returns:
        List of ClusterInfo objects, sorted by size (largest first)
    """
    points = np.asarray(pcd.points)
    num_clusters = labels.max() + 1
    
    cluster_infos = []
    
    for cluster_id in range(num_clusters):
        indices = np.where(labels == cluster_id)[0]
        if len(indices) > 0:
            cluster_points = points[indices]
            info = ClusterInfo(cluster_id, indices, cluster_points)
            cluster_infos.append(info)
    
    # Sort by number of points (largest first)
    cluster_infos.sort(key=lambda x: x.num_points, reverse=True)
    
    return cluster_infos


def colorize_by_clusters(
    pcd: o3d.geometry.PointCloud,
    labels: np.ndarray,
    noise_color: Tuple[float, float, float] = (0.5, 0.5, 0.5)
) -> o3d.geometry.PointCloud:
    """
    Colorize point cloud by cluster labels.
    
    Args:
        pcd: Input point cloud
        labels: Cluster labels (-1 for noise)
        noise_color: RGB color for noise points (default gray)
        
    Returns:
        Colorized point cloud (new copy)
    """
    pcd_colored = o3d.geometry.PointCloud(pcd)
    
    num_clusters = labels.max() + 1
    
    # Generate distinct colors for clusters
    if num_clusters > 0:
        # Use matplotlib's tab20 colormap for distinct colors
        cmap = plt.get_cmap('tab20')
        cluster_colors = [cmap(i % 20)[:3] for i in range(num_clusters)]
    else:
        cluster_colors = []
    
    # Assign colors
    colors = np.zeros((len(labels), 3))
    
    for i, label in enumerate(labels):
        if label == -1:
            colors[i] = noise_color
        else:
            colors[i] = cluster_colors[label % len(cluster_colors)]
    
    pcd_colored.colors = o3d.utility.Vector3dVector(colors)
    
    return pcd_colored


def highlight_cluster(
    pcd: o3d.geometry.PointCloud,
    labels: np.ndarray,
    cluster_id: int,
    highlight_color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
    other_color: Tuple[float, float, float] = (0.8, 0.8, 0.8)
) -> o3d.geometry.PointCloud:
    """
    Highlight a specific cluster, dim others.
    
    Args:
        pcd: Input point cloud
        labels: Cluster labels
        cluster_id: ID of cluster to highlight
        highlight_color: RGB color for highlighted cluster (default red)
        other_color: RGB color for other points (default light gray)
        
    Returns:
        Colorized point cloud (new copy)
    """
    pcd_colored = o3d.geometry.PointCloud(pcd)
    
    colors = np.full((len(labels), 3), other_color)
    
    # Highlight selected cluster
    cluster_mask = labels == cluster_id
    colors[cluster_mask] = highlight_color
    
    pcd_colored.colors = o3d.utility.Vector3dVector(colors)
    
    return pcd_colored


def isolate_cluster(
    pcd: o3d.geometry.PointCloud,
    labels: np.ndarray,
    cluster_id: int
) -> o3d.geometry.PointCloud:
    """
    Extract a single cluster as a separate point cloud.
    
    Args:
        pcd: Input point cloud
        labels: Cluster labels
        cluster_id: ID of cluster to extract
        
    Returns:
        Point cloud containing only the specified cluster
    """
    indices = np.where(labels == cluster_id)[0]
    cluster_pcd = pcd.select_by_index(indices.tolist())
    
    return cluster_pcd


def export_clusters(
    pcd: o3d.geometry.PointCloud,
    labels: np.ndarray,
    output_dir: str,
    base_name: str = "cluster"
) -> List[str]:
    """
    Export each cluster as a separate PLY file.
    
    Args:
        pcd: Input point cloud
        labels: Cluster labels
        output_dir: Directory to save cluster files
        base_name: Base name for files (default "cluster")
        
    Returns:
        List of saved file paths
    """
    import os
    
    num_clusters = labels.max() + 1
    saved_files = []
    
    for cluster_id in range(num_clusters):
        cluster_pcd = isolate_cluster(pcd, labels, cluster_id)
        
        if len(cluster_pcd.points) > 0:
            filename = f"{base_name}_{cluster_id:03d}.ply"
            filepath = os.path.join(output_dir, filename)
            
            o3d.io.write_point_cloud(filepath, cluster_pcd)
            saved_files.append(filepath)
    
    return saved_files


def get_clustering_stats(labels: np.ndarray) -> Dict:
    """
    Get detailed clustering statistics.
    
    Args:
        labels: Cluster labels
        
    Returns:
        Dictionary with statistics
    """
    num_clusters = labels.max() + 1
    num_noise = np.sum(labels == -1)
    num_clustered = len(labels) - num_noise
    
    cluster_sizes = []
    for i in range(num_clusters):
        size = np.sum(labels == i)
        cluster_sizes.append(size)
    
    stats = {
        'num_clusters': num_clusters,
        'num_noise': num_noise,
        'num_clustered': num_clustered,
        'cluster_sizes': cluster_sizes,
        'mean_cluster_size': np.mean(cluster_sizes) if cluster_sizes else 0,
        'max_cluster_size': max(cluster_sizes) if cluster_sizes else 0,
        'min_cluster_size': min(cluster_sizes) if cluster_sizes else 0
    }
    
    return stats
