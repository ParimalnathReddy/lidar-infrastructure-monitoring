"""
LiDAR Infrastructure Inspector - Point Cloud Loader
Supports: .ply, .pcd, .xyz, .txt (XYZ format), .las, .laz
"""
import os
import numpy as np
import open3d as o3d
from typing import Optional, Tuple


class LoaderError(Exception):
    """Custom exception for loader errors"""
    pass


def load_point_cloud(filepath: str) -> Tuple[o3d.geometry.PointCloud, dict]:
    """
    Load a point cloud from various formats.
    
    Args:
        filepath: Path to the point cloud file
        
    Returns:
        Tuple of (Open3D PointCloud object, metadata dict)
        
    Raises:
        LoaderError: If file cannot be loaded or is invalid
    """
    if not os.path.exists(filepath):
        raise LoaderError(f"File not found: {filepath}")
    
    ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if ext in ['.ply', '.pcd']:
            pcd = _load_open3d_format(filepath)
        elif ext in ['.xyz', '.txt']:
            pcd = _load_xyz_format(filepath)
        elif ext in ['.las', '.laz']:
            pcd = _load_las_format(filepath)
        else:
            raise LoaderError(f"Unsupported file format: {ext}")
        
        # Validate point cloud
        if not pcd.has_points():
            raise LoaderError("Point cloud is empty")
        
        # Compute metadata
        points = np.asarray(pcd.points)
        metadata = {
            'filename': os.path.basename(filepath),
            'point_count': len(points),
            'bounds': {
                'min': points.min(axis=0).tolist(),
                'max': points.max(axis=0).tolist()
            },
            'has_colors': pcd.has_colors(),
            'has_normals': pcd.has_normals()
        }
        
        return pcd, metadata
        
    except Exception as e:
        if isinstance(e, LoaderError):
            raise
        raise LoaderError(f"Failed to load {filepath}: {str(e)}")


def _load_open3d_format(filepath: str) -> o3d.geometry.PointCloud:
    """Load PLY or PCD format using Open3D"""
    pcd = o3d.io.read_point_cloud(filepath)
    if not pcd.has_points():
        raise LoaderError("Failed to read point cloud data")
    return pcd


def _load_xyz_format(filepath: str) -> o3d.geometry.PointCloud:
    """Load XYZ or TXT format (space/tab separated X Y Z [R G B])"""
    try:
        # Try to load as numpy array
        data = np.loadtxt(filepath)
        
        if data.ndim != 2:
            raise LoaderError("Invalid XYZ format: expected 2D array")
        
        if data.shape[1] < 3:
            raise LoaderError("Invalid XYZ format: need at least 3 columns (X Y Z)")
        
        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(data[:, :3])
        
        # Add colors if available (columns 4-6)
        if data.shape[1] >= 6:
            colors = data[:, 3:6]
            # Normalize if values are in 0-255 range
            if colors.max() > 1.0:
                colors = colors / 255.0
            pcd.colors = o3d.utility.Vector3dVector(colors)
        
        return pcd
        
    except Exception as e:
        raise LoaderError(f"Failed to parse XYZ file: {str(e)}")


def _load_las_format(filepath: str) -> o3d.geometry.PointCloud:
    """Load LAS/LAZ format using laspy"""
    try:
        import laspy
    except ImportError:
        raise LoaderError(
            "laspy not installed. Install with: pip install laspy[lazrs]"
        )
    
    try:
        las = laspy.read(filepath)
        
        # Extract XYZ coordinates
        points = np.vstack((las.x, las.y, las.z)).T
        
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        
        # Try to extract colors if available
        try:
            if hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue'):
                colors = np.vstack((las.red, las.green, las.blue)).T
                # LAS colors are typically 16-bit, normalize to 0-1
                colors = colors / 65535.0
                pcd.colors = o3d.utility.Vector3dVector(colors)
        except:
            pass  # Colors not available, continue without them
        
        return pcd
        
    except Exception as e:
        raise LoaderError(f"Failed to parse LAS/LAZ file: {str(e)}")


def get_point_cloud_info(pcd: o3d.geometry.PointCloud) -> str:
    """
    Get formatted string with point cloud information.
    
    Args:
        pcd: Open3D PointCloud object
        
    Returns:
        Formatted info string
    """
    points = np.asarray(pcd.points)
    info_lines = [
        f"Points: {len(points):,}",
        f"Bounds: X[{points[:, 0].min():.2f}, {points[:, 0].max():.2f}]",
        f"        Y[{points[:, 1].min():.2f}, {points[:, 1].max():.2f}]",
        f"        Z[{points[:, 2].min():.2f}, {points[:, 2].max():.2f}]"
    ]
    
    if pcd.has_colors():
        info_lines.append("Colors: Yes")
    if pcd.has_normals():
        info_lines.append("Normals: Yes")
    
    return " | ".join(info_lines)
