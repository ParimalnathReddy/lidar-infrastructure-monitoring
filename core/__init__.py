"""Core package for LiDAR Infrastructure Inspector"""
from .loader import load_point_cloud, LoaderError, get_point_cloud_info
from .registration import align_point_clouds_icp, apply_transformation, RegistrationResult
from .segmentation import remove_ground_plane, SegmentationResult
from .change_detection import compute_point_to_point_distances, colorize_by_distance, ChangeDetectionResult
from .clustering import (
    cluster_dbscan, extract_cluster_info, colorize_by_clusters,
    highlight_cluster, isolate_cluster, export_clusters,
    ClusterInfo, ClusteringResult
)
from .reporter import (
    ReportData, generate_preview_text, generate_pdf_report,
    save_histogram_plot
)
__all__ = [
    'load_point_cloud', 'LoaderError', 'get_point_cloud_info',
    'align_point_clouds_icp', 'apply_transformation', 'RegistrationResult',
    'remove_ground_plane', 'SegmentationResult',
    'compute_point_to_point_distances', 'colorize_by_distance', 'ChangeDetectionResult',
]
