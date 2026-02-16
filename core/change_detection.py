"""
LiDAR Infrastructure Inspector - Change Detection
Compute and visualize differences between point clouds
"""
import numpy as np
import open3d as o3d
from typing import Tuple, Optional
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


class ChangeDetectionResult:
    """Container for change detection results"""
    
    def __init__(self, distances: np.ndarray, signed: bool = False):
        self.distances = distances
        self.signed = signed  # True if signed distances (with direction)
        
        # Compute statistics
        self.mean = np.mean(distances)
        self.std = np.std(distances)
        self.min = np.min(distances)
        self.max = np.max(distances)
        self.median = np.median(distances)
    
    def get_statistics_str(self) -> str:
        """Get human-readable statistics"""
        if self.signed:
            return (f"Mean: {self.mean:.3f}m | Std: {self.std:.3f}m | "
                   f"Range: [{self.min:.3f}, {self.max:.3f}]m")
        else:
            return (f"Mean: {self.mean:.3f}m | Std: {self.std:.3f}m | "
                   f"Max: {self.max:.3f}m")
    
    def __repr__(self):
        return f"ChangeDetectionResult(mean={self.mean:.3f}m, std={self.std:.3f}m)"


def compute_point_to_point_distances(
    source: o3d.geometry.PointCloud,
    target: o3d.geometry.PointCloud,
    use_normals: bool = True
) -> ChangeDetectionResult:
    """
    Compute distances from source to target point cloud.
    
    Args:
        source: Source point cloud (typically Target after alignment)
        target: Target point cloud (typically Reference)
        use_normals: If True and normals exist, compute signed distances
        
    Returns:
        ChangeDetectionResult with distance array and statistics
    """
    source_points = np.asarray(source.points)
    target_points = np.asarray(target.points)
    
    # Build KDTree for target
    target_tree = o3d.geometry.KDTreeFlann(target)
    
    distances = []
    signed = False
    
    # Check if we can compute signed distances
    if use_normals and source.has_normals() and target.has_normals():
        signed = True
        source_normals = np.asarray(source.normals)
        target_normals = np.asarray(target.normals)
        
        for i, point in enumerate(source_points):
            # Find nearest neighbor in target
            [k, idx, dist_sq] = target_tree.search_knn_vector_3d(point, 1)
            
            if k > 0:
                nearest_idx = idx[0]
                nearest_point = target_points[nearest_idx]
                nearest_normal = target_normals[nearest_idx]
                
                # Compute signed distance using normal
                diff = point - nearest_point
                signed_dist = np.dot(diff, nearest_normal)
                distances.append(signed_dist)
            else:
                distances.append(0.0)
    else:
        # Unsigned distances (magnitude only)
        for point in source_points:
            [k, idx, dist_sq] = target_tree.search_knn_vector_3d(point, 1)
            
            if k > 0:
                dist = np.sqrt(dist_sq[0])
                distances.append(dist)
            else:
                distances.append(0.0)
    
    distances = np.array(distances)
    
    return ChangeDetectionResult(distances, signed=signed)


def colorize_by_distance(
    pcd: o3d.geometry.PointCloud,
    distances: np.ndarray,
    signed: bool = False,
    colormap: str = 'RdYlBu_r'
) -> o3d.geometry.PointCloud:
    """
    Colorize point cloud based on distance values.
    
    Args:
        pcd: Point cloud to colorize
        distances: Distance array (same length as points)
        signed: If True, use diverging colormap centered at 0
        colormap: Matplotlib colormap name
        
    Returns:
        Colorized point cloud (new copy)
    """
    pcd_colored = o3d.geometry.PointCloud(pcd)
    
    # Normalize distances to [0, 1]
    if signed:
        # Diverging colormap: negative (blue) to positive (red)
        # Center at 0
        max_abs = max(abs(distances.min()), abs(distances.max()))
        if max_abs > 0:
            normalized = (distances + max_abs) / (2 * max_abs)
        else:
            normalized = np.zeros_like(distances)
    else:
        # Sequential colormap: 0 (blue) to max (red)
        d_min, d_max = distances.min(), distances.max()
        if d_max > d_min:
            normalized = (distances - d_min) / (d_max - d_min)
        else:
            normalized = np.zeros_like(distances)
    
    # Apply colormap
    cmap = plt.get_cmap(colormap)
    colors = cmap(normalized)[:, :3]  # RGB only, no alpha
    
    pcd_colored.colors = o3d.utility.Vector3dVector(colors)
    
    return pcd_colored


def create_distance_histogram(
    distances: np.ndarray,
    signed: bool = False,
    bins: int = 50,
    title: str = "Distance Distribution"
) -> plt.Figure:
    """
    Create histogram of distance distribution.
    
    Args:
        distances: Distance array
        signed: If True, show signed distances
        bins: Number of histogram bins
        title: Plot title
        
    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.hist(distances, bins=bins, color='steelblue', edgecolor='black', alpha=0.7)
    
    # Add statistics
    mean = np.mean(distances)
    std = np.std(distances)
    median = np.median(distances)
    
    ax.axvline(mean, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean:.3f}m')
    ax.axvline(median, color='green', linestyle='--', linewidth=2, label=f'Median: {median:.3f}m')
    
    if signed:
        ax.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        ax.set_xlabel('Signed Distance (m)\n(Negative = Loss/Erosion, Positive = Gain/Deposition)')
    else:
        ax.set_xlabel('Distance Magnitude (m)')
    
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add text box with statistics
    stats_text = f'μ = {mean:.3f}m\nσ = {std:.3f}m\nMin = {distances.min():.3f}m\nMax = {distances.max():.3f}m'
    ax.text(0.98, 0.97, stats_text,
            transform=ax.transAxes,
            verticalalignment='top',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            fontsize=9)
    
    plt.tight_layout()
    
    return fig


def classify_changes(
    distances: np.ndarray,
    threshold: float = 0.05,
    signed: bool = False
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Classify points into change categories.
    
    Args:
        distances: Distance array
        threshold: Threshold for "no change" classification
        signed: If True, classify as erosion/deposition
        
    Returns:
        Tuple of (no_change_mask, erosion_mask, deposition_mask)
        For unsigned: erosion_mask is all False, deposition_mask is significant changes
    """
    if signed:
        no_change = np.abs(distances) < threshold
        erosion = distances < -threshold  # Negative = loss
        deposition = distances > threshold  # Positive = gain
    else:
        no_change = distances < threshold
        erosion = np.zeros_like(distances, dtype=bool)  # Not applicable
        deposition = distances >= threshold
    
    return no_change, erosion, deposition


def get_change_summary(
    result: ChangeDetectionResult,
    threshold: float = 0.05
) -> str:
    """
    Get human-readable change summary.
    
    Args:
        result: ChangeDetectionResult
        threshold: Threshold for change classification
        
    Returns:
        Summary string
    """
    no_change, erosion, deposition = classify_changes(
        result.distances, threshold, result.signed
    )
    
    total = len(result.distances)
    no_change_pct = (no_change.sum() / total) * 100
    
    if result.signed:
        erosion_pct = (erosion.sum() / total) * 100
        deposition_pct = (deposition.sum() / total) * 100
        
        return (f"No change: {no_change_pct:.1f}% | "
                f"Erosion: {erosion_pct:.1f}% | "
                f"Deposition: {deposition_pct:.1f}%")
    else:
        change_pct = 100 - no_change_pct
        return (f"No change: {no_change_pct:.1f}% | "
                f"Significant change: {change_pct:.1f}%")
