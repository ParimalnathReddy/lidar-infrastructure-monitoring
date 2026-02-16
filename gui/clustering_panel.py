"""
LiDAR Infrastructure Inspector - Clustering Panel
Interactive DBSCAN clustering with real-time slider controls
"""
import os
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QSlider, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont
import open3d as o3d

from core.clustering import (
    cluster_dbscan, extract_cluster_info, colorize_by_clusters,
    highlight_cluster, export_clusters, ClusteringResult
)


class ClusteringWorker(QObject):
    """Worker for running DBSCAN in background thread"""
    
    # Signals
    progress = pyqtSignal(str)
    finished = pyqtSignal(object, object)  # (labels, result)
    error = pyqtSignal(str)
    
    def __init__(self, pcd, eps, min_samples, filter_by_distance=False,
                 distance_threshold=0.1, distances=None):
        super().__init__()
        self.pcd = pcd
        self.eps = eps
        self.min_samples = min_samples
        self.filter_by_distance = filter_by_distance
        self.distance_threshold = distance_threshold
        self.distances = distances
    
    def run(self):
        """Run DBSCAN clustering"""
        try:
            self.progress.emit(f"Running DBSCAN (eps={self.eps:.2f}, min_samples={self.min_samples})...")
            
            labels, result = cluster_dbscan(
                self.pcd,
                eps=self.eps,
                min_samples=self.min_samples,
                filter_by_distance=self.filter_by_distance,
                distance_threshold=self.distance_threshold,
                distances=self.distances
            )
            
            self.progress.emit(f"Clustering complete: {result.get_summary()}")
            self.finished.emit(labels, result)
            
        except Exception as e:
            self.error.emit(str(e))


class ClusteringPanel(QWidget):
    """Clustering panel with interactive DBSCAN controls"""
    
    # Signals
    cloud_updated = pyqtSignal(str, object)  # (cloud_type, point_cloud)
    clustering_completed = pyqtSignal(float, int, float, int, int, list)  # (eps, min_samples, threshold, num_clusters, num_noise, cluster_infos)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_cloud = None
        self.current_distances = None
        self.labels = None
        self.cluster_infos = []
        self.clustering_result = None
        
        self.worker_thread = None
        self.worker = None
        
        # Debounce timer
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._run_clustering)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # DBSCAN Parameters Section
        params_group = self._create_parameters_section()
        layout.addWidget(params_group)
        
        # Cluster List Section
        list_group = self._create_cluster_list_section()
        layout.addWidget(list_group, 1)
        
        # Export Section
        export_group = self._create_export_section()
        layout.addWidget(export_group)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        # Status Label
        self.status_label = QLabel("Load point cloud and run change detection first")
        self.status_label.setStyleSheet("padding: 5px; background-color: #ecf0f1; border-radius: 3px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def _create_parameters_section(self) -> QGroupBox:
        """Create DBSCAN parameter controls"""
        group = QGroupBox("DBSCAN Parameters")
        layout = QVBoxLayout()
        
        # Eps slider
        eps_layout = QHBoxLayout()
        eps_layout.addWidget(QLabel("Epsilon (m):"))
        
        self.eps_slider = QSlider(Qt.Horizontal)
        self.eps_slider.setMinimum(5)  # 0.05m
        self.eps_slider.setMaximum(200)  # 2.0m
        self.eps_slider.setValue(50)  # 0.5m default
        self.eps_slider.setTickPosition(QSlider.TicksBelow)
        self.eps_slider.setTickInterval(20)
        self.eps_slider.valueChanged.connect(self._on_slider_changed)
        
        self.eps_label = QLabel("0.50")
        self.eps_label.setMinimumWidth(50)
        
        eps_layout.addWidget(self.eps_slider)
        eps_layout.addWidget(self.eps_label)
        layout.addLayout(eps_layout)
        
        # Min samples slider
        min_samples_layout = QHBoxLayout()
        min_samples_layout.addWidget(QLabel("Min Samples:"))
        
        self.min_samples_slider = QSlider(Qt.Horizontal)
        self.min_samples_slider.setMinimum(3)
        self.min_samples_slider.setMaximum(200)
        self.min_samples_slider.setValue(10)
        self.min_samples_slider.setTickPosition(QSlider.TicksBelow)
        self.min_samples_slider.setTickInterval(20)
        self.min_samples_slider.valueChanged.connect(self._on_slider_changed)
        
        self.min_samples_label = QLabel("10")
        self.min_samples_label.setMinimumWidth(50)
        
        min_samples_layout.addWidget(self.min_samples_slider)
        min_samples_layout.addWidget(self.min_samples_label)
        layout.addLayout(min_samples_layout)
        
        # Change threshold slider (optional filtering)
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Change Threshold (m):"))
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(0)  # 0.0m (no filtering)
        self.threshold_slider.setMaximum(100)  # 1.0m
        self.threshold_slider.setValue(10)  # 0.1m default
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.valueChanged.connect(self._on_slider_changed)
        
        self.threshold_label = QLabel("0.10")
        self.threshold_label.setMinimumWidth(50)
        
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)
        layout.addLayout(threshold_layout)
        
        # Run button
        self.run_btn = QPushButton("Run Clustering")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.run_btn.clicked.connect(self._trigger_clustering)
        self.run_btn.setEnabled(False)
        layout.addWidget(self.run_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_cluster_list_section(self) -> QGroupBox:
        """Create cluster list widget"""
        group = QGroupBox("Clusters")
        layout = QVBoxLayout()
        
        # Cluster list
        self.cluster_list = QListWidget()
        self.cluster_list.setFont(QFont("Courier", 9))
        self.cluster_list.itemClicked.connect(self._on_cluster_selected)
        layout.addWidget(self.cluster_list)
        
        # Highlight/Reset buttons
        button_layout = QHBoxLayout()
        
        self.highlight_btn = QPushButton("Highlight Selected")
        self.highlight_btn.clicked.connect(self._highlight_selected_cluster)
        self.highlight_btn.setEnabled(False)
        
        self.reset_colors_btn = QPushButton("Reset Colors")
        self.reset_colors_btn.clicked.connect(self._reset_cluster_colors)
        self.reset_colors_btn.setEnabled(False)
        
        button_layout.addWidget(self.highlight_btn)
        button_layout.addWidget(self.reset_colors_btn)
        layout.addLayout(button_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_export_section(self) -> QGroupBox:
        """Create export controls"""
        group = QGroupBox("Export")
        layout = QVBoxLayout()
        
        self.export_btn = QPushButton("Export All Clusters")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138d75;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.export_btn.clicked.connect(self._export_clusters)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)
        
        group.setLayout(layout)
        return group
    
    def set_point_cloud(self, pcd: o3d.geometry.PointCloud, distances: np.ndarray = None):
        """
        Set point cloud for clustering.
        
        Args:
            pcd: Point cloud to cluster
            distances: Optional distance array for filtering
        """
        self.current_cloud = pcd
        self.current_distances = distances
        self.labels = None
        self.cluster_infos = []
        
        # Enable controls
        self.run_btn.setEnabled(pcd is not None)
        
        # Clear cluster list
        self.cluster_list.clear()
        self.highlight_btn.setEnabled(False)
        self.reset_colors_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        if pcd is not None:
            self.status_label.setText(f"Ready to cluster {len(pcd.points):,} points")
        else:
            self.status_label.setText("Load point cloud and run change detection first")
    
    def _on_slider_changed(self):
        """Handle slider value changes with debouncing"""
        # Update labels
        eps = self.eps_slider.value() / 100.0
        self.eps_label.setText(f"{eps:.2f}")
        
        min_samples = self.min_samples_slider.value()
        self.min_samples_label.setText(str(min_samples))
        
        threshold = self.threshold_slider.value() / 100.0
        self.threshold_label.setText(f"{threshold:.2f}")
        
        # Restart debounce timer (300ms delay)
        self.debounce_timer.stop()
        self.debounce_timer.start(300)
    
    def _trigger_clustering(self):
        """Manually trigger clustering (button click)"""
        self.debounce_timer.stop()
        self._run_clustering()
    
    def _run_clustering(self):
        """Run DBSCAN clustering in background thread"""
        if self.current_cloud is None:
            return
        
        # Get parameters
        eps = self.eps_slider.value() / 100.0
        min_samples = self.min_samples_slider.value()
        threshold = self.threshold_slider.value() / 100.0
        
        # Determine if we should filter by distance
        filter_by_distance = (self.current_distances is not None and threshold > 0)
        
        # Disable controls
        self.run_btn.setEnabled(False)
        self.eps_slider.setEnabled(False)
        self.min_samples_slider.setEnabled(False)
        self.threshold_slider.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        
        # Create worker
        self.worker = ClusteringWorker(
            self.current_cloud,
            eps=eps,
            min_samples=min_samples,
            filter_by_distance=filter_by_distance,
            distance_threshold=threshold,
            distances=self.current_distances
        )
        
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_clustering_finished)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self._cleanup_worker)
        
        # Start thread
        self.worker_thread.start()
    
    def _on_progress(self, message: str):
        """Handle progress updates"""
        self.status_label.setText(message)
    
    def _on_clustering_finished(self, labels, result: ClusteringResult):
        """Handle clustering completion"""
        self.labels = labels
        self.clustering_result = result
        
        # Extract cluster info
        self.cluster_infos = extract_cluster_info(self.current_cloud, labels)
        
        # Update cluster list
        self._update_cluster_list()
        
        # Colorize by clusters
        colored_cloud = colorize_by_clusters(self.current_cloud, labels)
        self.cloud_updated.emit('target', colored_cloud)
        
        # Update status
        self.status_label.setText(result.get_summary())
        
        # Enable export if clusters found
        self.export_btn.setEnabled(result.num_clusters > 0)
        self.reset_colors_btn.setEnabled(True)
        
        # Emit signal for report panel
        eps = self.eps_slider.value() / 100.0
        min_samples = self.min_samples_slider.value()
        threshold = self.threshold_slider.value() / 100.0
        self.clustering_completed.emit(
            eps, min_samples, threshold,
            result.num_clusters, result.num_noise,
            self.cluster_infos
        )
    
    def _on_error(self, error_msg: str):
        """Handle errors"""
        self.status_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(self, "Clustering Error", f"An error occurred:\n{error_msg}")
    
    def _cleanup_worker(self):
        """Clean up worker thread"""
        self.progress_bar.setVisible(False)
        
        # Re-enable controls
        self.run_btn.setEnabled(True)
        self.eps_slider.setEnabled(True)
        self.min_samples_slider.setEnabled(True)
        self.threshold_slider.setEnabled(True)
        
        # Clean up thread
        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def _update_cluster_list(self):
        """Update cluster list widget"""
        self.cluster_list.clear()
        
        for info in self.cluster_infos:
            item_text = (f"Cluster {info.cluster_id:3d} | "
                        f"{info.num_points:6,} pts | "
                        f"Vol: {info.volume:8.3f} m³")
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, info.cluster_id)
            self.cluster_list.addItem(item)
        
        self.highlight_btn.setEnabled(len(self.cluster_infos) > 0)
    
    def _on_cluster_selected(self, item: QListWidgetItem):
        """Handle cluster selection"""
        cluster_id = item.data(Qt.UserRole)
        
        # Find cluster info
        cluster_info = None
        for info in self.cluster_infos:
            if info.cluster_id == cluster_id:
                cluster_info = info
                break
        
        if cluster_info:
            # Update status with cluster details
            self.status_label.setText(
                f"Selected: {cluster_info} | "
                f"Centroid: ({cluster_info.centroid[0]:.1f}, "
                f"{cluster_info.centroid[1]:.1f}, "
                f"{cluster_info.centroid[2]:.1f})"
            )
    
    def _highlight_selected_cluster(self):
        """Highlight the selected cluster"""
        current_item = self.cluster_list.currentItem()
        
        if current_item is None:
            QMessageBox.warning(self, "No Selection", "Please select a cluster first")
            return
        
        cluster_id = current_item.data(Qt.UserRole)
        
        # Highlight cluster
        highlighted_cloud = highlight_cluster(self.current_cloud, self.labels, cluster_id)
        self.cloud_updated.emit('target', highlighted_cloud)
        
        self.status_label.setText(f"Highlighted cluster {cluster_id}")
    
    def _reset_cluster_colors(self):
        """Reset to cluster colors"""
        if self.labels is not None:
            colored_cloud = colorize_by_clusters(self.current_cloud, self.labels)
            self.cloud_updated.emit('target', colored_cloud)
            self.status_label.setText("Reset to cluster colors")
    
    def _export_clusters(self):
        """Export all clusters to PLY files"""
        if self.labels is None or self.clustering_result.num_clusters == 0:
            QMessageBox.warning(self, "No Clusters", "No clusters to export")
            return
        
        # Select output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory for Clusters",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if not output_dir:
            return
        
        try:
            self.status_label.setText("Exporting clusters...")
            
            saved_files = export_clusters(
                self.current_cloud,
                self.labels,
                output_dir,
                base_name="cluster"
            )
            
            self.status_label.setText(f"Exported {len(saved_files)} clusters to {output_dir}")
            
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {len(saved_files)} clusters to:\n{output_dir}"
            )
            
        except Exception as e:
            self.status_label.setText(f"Export failed: {str(e)}")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export clusters:\n{str(e)}"
            )
