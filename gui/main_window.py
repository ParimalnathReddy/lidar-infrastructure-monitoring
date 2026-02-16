"""
LiDAR Infrastructure Inspector - Main Window
Dual viewport application for comparing point clouds
"""
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFileDialog, QStatusBar, QMessageBox,
    QSplitter, QTabWidget
)
from PyQt5.QtCore import Qt
from .viewer_widget import ViewerWidget
from .analysis_panel import AnalysisPanel
from .clustering_panel import ClusteringPanel
from .report_panel import ReportPanel
from core.loader import load_point_cloud, LoaderError, get_point_cloud_info


class MainWindow(QMainWindow):
    """Main application window with dual viewport"""
    
    def __init__(self):
        super().__init__()
        self.ref_cloud = None
        self.target_cloud = None
        self.ref_metadata = None
        self.target_metadata = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Infrastructure Inspector")
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Button panel
        button_layout = QHBoxLayout()
        
        self.load_ref_btn = QPushButton("Load Reference")
        self.load_ref_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.load_ref_btn.clicked.connect(self.load_reference)
        
        self.load_target_btn = QPushButton("Load Target")
        self.load_target_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.load_target_btn.clicked.connect(self.load_target)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_all)
        
        button_layout.addWidget(self.load_ref_btn)
        button_layout.addWidget(self.load_target_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(button_layout, 0)
        
        # Main content area (viewers + analysis panel)
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left: Dual viewport
        viewer_splitter = QSplitter(Qt.Horizontal)
        
        self.ref_viewer = ViewerWidget("Reference (Left)", self)
        self.ref_viewer.file_dropped.connect(self.on_ref_dropped)
        
        self.target_viewer = ViewerWidget("Target (Right)", self)
        self.target_viewer.file_dropped.connect(self.on_target_dropped)
        
        viewer_splitter.addWidget(self.ref_viewer)
        viewer_splitter.addWidget(self.target_viewer)
        viewer_splitter.setStretchFactor(0, 1)
        viewer_splitter.setStretchFactor(1, 1)
        
        # Right: Analysis panel in tabs
        self.tab_widget = QTabWidget()
        
        # Analysis tab
        self.analysis_panel = AnalysisPanel(self)
        self.analysis_panel.cloud_updated.connect(self.on_cloud_updated)
        self.tab_widget.addTab(self.analysis_panel, "Analysis")
        
        # Clustering tab
        self.clustering_panel = ClusteringPanel(self)
        self.clustering_panel.cloud_updated.connect(self.on_cloud_updated)
        self.tab_widget.addTab(self.clustering_panel, "Clustering")
        
        # Report tab
        self.report_panel = ReportPanel(self)
        self.tab_widget.addTab(self.report_panel, "Report")
        
        # Connect analysis to clustering (pass change detection results)
        self.analysis_panel.change_detected.connect(self.on_change_detected)
        
        # Connect analysis/clustering to report panel
        self.analysis_panel.icp_completed.connect(self.report_panel.set_icp_results)
        self.analysis_panel.ground_removed.connect(self.report_panel.set_ground_removal_results)
        self.analysis_panel.change_detected.connect(self.on_change_detected_for_report)
        self.clustering_panel.clustering_completed.connect(self.report_panel.set_clustering_results)
        
        # Add to main splitter
        content_splitter.addWidget(viewer_splitter)
        content_splitter.addWidget(self.tab_widget)
        content_splitter.setStretchFactor(0, 1)
        content_splitter.setStretchFactor(1, 0)
        
        main_layout.addWidget(content_splitter, 1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Load point clouds to begin.")
    
    def load_reference(self):
        """Load reference point cloud via file dialog"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Reference Point Cloud",
            "",
            "Point Clouds (*.ply *.pcd *.xyz *.txt *.las *.laz);;All Files (*)"
        )
        
        if filepath:
            self._load_cloud(filepath, is_reference=True)
    
    def load_target(self):
        """Load target point cloud via file dialog"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Target Point Cloud",
            "",
            "Point Clouds (*.ply *.pcd *.xyz *.txt *.las *.laz);;All Files (*)"
        )
        
        if filepath:
            self._load_cloud(filepath, is_reference=False)
    
    def on_ref_dropped(self, filepath: str):
        """Handle file dropped on reference viewer"""
        self._load_cloud(filepath, is_reference=True)
    
    def on_target_dropped(self, filepath: str):
        """Handle file dropped on target viewer"""
        self._load_cloud(filepath, is_reference=False)
    
    def _load_cloud(self, filepath: str, is_reference: bool):
        """
        Load a point cloud file.
        
        Args:
            filepath: Path to the point cloud file
            is_reference: True for reference cloud, False for target
        """
        try:
            self.status_bar.showMessage(f"Loading {filepath}...")
            
            # Load point cloud
            pcd, metadata = load_point_cloud(filepath)
            
            # Store and display
            if is_reference:
                self.ref_cloud = pcd
                self.ref_metadata = metadata
                self.ref_viewer.load_point_cloud(pcd, metadata['filename'])
                status_msg = f"Reference: {metadata['filename']} | {metadata['point_count']:,} points"
            else:
                self.target_cloud = pcd
                self.target_metadata = metadata
                self.target_viewer.load_point_cloud(pcd, metadata['filename'])
                status_msg = f"Target: {metadata['filename']} | {metadata['point_count']:,} points"
            
            # Update status bar with bounds info
            bounds = metadata['bounds']
            status_msg += f" | Bounds: X[{bounds['min'][0]:.1f}, {bounds['max'][0]:.1f}] "
            status_msg += f"Y[{bounds['min'][1]:.1f}, {bounds['max'][1]:.1f}] "
            status_msg += f"Z[{bounds['min'][2]:.1f}, {bounds['max'][2]:.1f}]"
            
            self.status_bar.showMessage(status_msg)
            
            # Update analysis panel with both clouds
            self.analysis_panel.set_point_clouds(self.ref_cloud, self.target_cloud)
            
            # Update report panel with file info
            if self.ref_cloud and self.target_cloud:
                self.report_panel.set_file_info(
                    self.ref_metadata['filename'],
                    self.target_metadata['filename'],
                    self.ref_metadata['point_count'],
                    self.target_metadata['point_count']
                )
                # Capture screenshots
                self.report_panel.capture_screenshots_from_viewers(
                    self.ref_viewer, self.target_viewer
                )
            
        except LoaderError as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load point cloud:\n{str(e)}"
            )
            self.status_bar.showMessage("Load failed.")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n{str(e)}"
            )
            self.status_bar.showMessage("Load failed.")
    
    def on_cloud_updated(self, cloud_type: str, pcd):
        """
        Handle cloud updates from analysis panel.
        
        Args:
            cloud_type: 'reference' or 'target'
            pcd: Updated point cloud
        """
        if cloud_type == 'target':
            self.target_viewer.load_point_cloud(pcd, "Processed Target")
            self.status_bar.showMessage("Target cloud updated from analysis")
        elif cloud_type == 'reference':
            self.ref_viewer.load_point_cloud(pcd, "Processed Reference")
            self.status_bar.showMessage("Reference cloud updated from analysis")
    
    def on_change_detected(self, cloud, distances, result):
        """
        Handle change detection completion.
        
        Args:
            cloud: Aligned target point cloud
            distances: Distance array
            result: ChangeDetectionResult
        """
        # Update clustering panel with change detection results
        self.clustering_panel.set_point_cloud(cloud, distances)
        self.status_bar.showMessage(f"Change detection complete. Ready for clustering.")
    
    def on_change_detected_for_report(self, cloud, distances, result):
        """
        Handle change detection for report panel.
        
        Args:
            cloud: Aligned target point cloud
            distances: Distance array
            result: ChangeDetectionResult
        """
        # Update report panel with change detection results
        self.report_panel.set_change_detection_results(distances, result.signed)
        # Capture updated screenshots
        self.report_panel.capture_screenshots_from_viewers(
            self.ref_viewer, self.target_viewer
        )
    
    def clear_all(self):
        """Clear both viewers"""
        self.ref_cloud = None
        self.target_cloud = None
        self.ref_metadata = None
        self.target_metadata = None
        
        self.ref_viewer.clear()
        self.target_viewer.clear()
        
        # Reset analysis panel
        self.analysis_panel.set_point_clouds(None, None)
        
        # Reset clustering panel
        self.clustering_panel.set_point_cloud(None, None)
        
        self.status_bar.showMessage("Cleared. Ready to load new point clouds.")
