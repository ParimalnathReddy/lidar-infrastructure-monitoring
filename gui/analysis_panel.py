"""
LiDAR Infrastructure Inspector - Analysis Panel
GUI controls for ICP alignment, ground removal, and change detection
"""
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QSlider, QTextEdit, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import open3d as o3d

from core.registration import align_point_clouds_icp, apply_transformation, RegistrationResult
from core.segmentation import remove_ground_plane, get_ground_removal_stats
from core.change_detection import (
    compute_point_to_point_distances, colorize_by_distance,
    create_distance_histogram, get_change_summary
)


class AnalysisWorker(QObject):
    """Worker for running analysis tasks in background thread"""
    
    # Signals
    progress = pyqtSignal(int, str)  # (percentage, message)
    finished = pyqtSignal(object)  # Result object
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, task_type: str, **kwargs):
        super().__init__()
        self.task_type = task_type
        self.kwargs = kwargs
        self._is_cancelled = False
    
    def cancel(self):
        """Cancel the operation"""
        self._is_cancelled = True
    
    def run(self):
        """Run the analysis task"""
        try:
            if self.task_type == 'icp':
                self._run_icp()
            elif self.task_type == 'ground_removal':
                self._run_ground_removal()
            elif self.task_type == 'change_detection':
                self._run_change_detection()
        except Exception as e:
            self.error.emit(str(e))
    
    def _run_icp(self):
        """Run ICP alignment"""
        source = self.kwargs['source']
        target = self.kwargs['target']
        max_distance = self.kwargs.get('max_distance', 0.5)
        max_iterations = self.kwargs.get('max_iterations', 50)
        
        def progress_callback(iteration, rmse):
            if self._is_cancelled:
                return False
            pct = int((iteration / max_iterations) * 100)
            self.progress.emit(pct, f"ICP Iteration {iteration}/{max_iterations} - RMSE: {rmse:.4f}")
            return True
        
        self.progress.emit(0, "Starting ICP alignment...")
        
        result = align_point_clouds_icp(
            source, target,
            max_correspondence_distance=max_distance,
            max_iterations=max_iterations,
            progress_callback=progress_callback
        )
        
        if not self._is_cancelled:
            self.progress.emit(100, "ICP alignment complete")
            self.finished.emit(result)
    
    def _run_ground_removal(self):
        """Run ground plane removal"""
        pcd = self.kwargs['pcd']
        threshold = self.kwargs.get('threshold', 0.2)
        
        self.progress.emit(50, "Detecting ground plane...")
        
        ground, non_ground, seg_result = remove_ground_plane(
            pcd, distance_threshold=threshold
        )
        
        self.progress.emit(100, "Ground removal complete")
        self.finished.emit((ground, non_ground, seg_result))
    
    def _run_change_detection(self):
        """Run change detection"""
        source = self.kwargs['source']
        target = self.kwargs['target']
        use_normals = self.kwargs.get('use_normals', True)
        
        self.progress.emit(50, "Computing distances...")
        
        result = compute_point_to_point_distances(source, target, use_normals)
        
        self.progress.emit(75, "Colorizing point cloud...")
        
        colorized = colorize_by_distance(source, result.distances, result.signed)
        
        self.progress.emit(100, "Change detection complete")
        self.finished.emit((result, colorized))


class AnalysisPanel(QWidget):
    """Analysis panel with ICP, ground removal, and change detection controls"""
    
    # Signals
    cloud_updated = pyqtSignal(str, object)  # (cloud_type, point_cloud)
    change_detected = pyqtSignal(object, object, object)  # (cloud, distances, result)
    icp_completed = pyqtSignal(float, float, int)  # (fitness, rmse, iterations)
    ground_removed = pyqtSignal(float, int, int)  # (threshold, ground_pts, non_ground_pts)
    clustering_completed = pyqtSignal(float, int, float, int, int, list)  # (eps, min_samples, threshold, num_clusters, num_noise, cluster_infos)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.ref_cloud = None
        self.target_cloud = None
        self.aligned_target = None
        self.change_result = None
        
        self.worker_thread = None
        self.worker = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # ICP Alignment Section
        icp_group = self._create_icp_section()
        layout.addWidget(icp_group)
        
        # Ground Removal Section
        ground_group = self._create_ground_removal_section()
        layout.addWidget(ground_group)
        
        # Change Detection Section
        change_group = self._create_change_detection_section()
        layout.addWidget(change_group)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status/Log Area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Courier", 9))
        layout.addWidget(QLabel("Analysis Log:"))
        layout.addWidget(self.log_text)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _create_icp_section(self) -> QGroupBox:
        """Create ICP alignment controls"""
        group = QGroupBox("1. Scan Alignment (ICP)")
        layout = QVBoxLayout()
        
        # Align button
        self.align_btn = QPushButton("Align Scans (ICP)")
        self.align_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.align_btn.clicked.connect(self.run_icp_alignment)
        self.align_btn.setEnabled(False)
        layout.addWidget(self.align_btn)
        
        # Metrics display
        self.icp_metrics_label = QLabel("Metrics: Not yet aligned")
        self.icp_metrics_label.setStyleSheet("padding: 5px; background-color: #ecf0f1; border-radius: 3px;")
        layout.addWidget(self.icp_metrics_label)
        
        # Convergence plot placeholder
        self.icp_figure = plt.Figure(figsize=(5, 2))
        self.icp_canvas = FigureCanvas(self.icp_figure)
        self.icp_canvas.setMaximumHeight(150)
        layout.addWidget(self.icp_canvas)
        
        group.setLayout(layout)
        return group
    
    def _create_ground_removal_section(self) -> QGroupBox:
        """Create ground removal controls"""
        group = QGroupBox("2. Ground Removal")
        layout = QVBoxLayout()
        
        # Threshold slider
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Ground Threshold (m):"))
        
        self.ground_threshold_slider = QSlider(Qt.Horizontal)
        self.ground_threshold_slider.setMinimum(10)  # 0.1m
        self.ground_threshold_slider.setMaximum(50)  # 0.5m
        self.ground_threshold_slider.setValue(20)  # 0.2m default
        self.ground_threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.ground_threshold_slider.setTickInterval(10)
        self.ground_threshold_slider.valueChanged.connect(self._update_ground_threshold_label)
        
        self.ground_threshold_label = QLabel("0.20")
        self.ground_threshold_label.setMinimumWidth(40)
        
        slider_layout.addWidget(self.ground_threshold_slider)
        slider_layout.addWidget(self.ground_threshold_label)
        layout.addLayout(slider_layout)
        
        # Remove ground button
        self.remove_ground_btn = QPushButton("Remove Ground")
        self.remove_ground_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.remove_ground_btn.clicked.connect(self.run_ground_removal)
        self.remove_ground_btn.setEnabled(False)
        layout.addWidget(self.remove_ground_btn)
        
        # Stats display
        self.ground_stats_label = QLabel("Stats: No ground removal yet")
        self.ground_stats_label.setStyleSheet("padding: 5px; background-color: #ecf0f1; border-radius: 3px;")
        self.ground_stats_label.setWordWrap(True)
        layout.addWidget(self.ground_stats_label)
        
        group.setLayout(layout)
        return group
    
    def _create_change_detection_section(self) -> QGroupBox:
        """Create change detection controls"""
        group = QGroupBox("3. Change Detection")
        layout = QVBoxLayout()
        
        # Compute change map button
        self.change_map_btn = QPushButton("Compute Change Map")
        self.change_map_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.change_map_btn.clicked.connect(self.run_change_detection)
        self.change_map_btn.setEnabled(False)
        layout.addWidget(self.change_map_btn)
        
        # Stats display
        self.change_stats_label = QLabel("Stats: No change detection yet")
        self.change_stats_label.setStyleSheet("padding: 5px; background-color: #ecf0f1; border-radius: 3px;")
        self.change_stats_label.setWordWrap(True)
        layout.addWidget(self.change_stats_label)
        
        # Histogram
        self.hist_figure = plt.Figure(figsize=(5, 2.5))
        self.hist_canvas = FigureCanvas(self.hist_figure)
        self.hist_canvas.setMaximumHeight(200)
        layout.addWidget(self.hist_canvas)
        
        group.setLayout(layout)
        return group
    
    def set_point_clouds(self, ref_cloud: o3d.geometry.PointCloud, 
                        target_cloud: o3d.geometry.PointCloud):
        """Set reference and target point clouds"""
        self.ref_cloud = ref_cloud
        self.target_cloud = target_cloud
        self.aligned_target = None
        self.change_result = None
        
        # Enable/disable buttons
        both_loaded = ref_cloud is not None and target_cloud is not None
        self.align_btn.setEnabled(both_loaded)
        self.remove_ground_btn.setEnabled(target_cloud is not None)
        self.change_map_btn.setEnabled(False)
        
        self.log("Point clouds loaded. Ready for analysis.")
    
    def _update_ground_threshold_label(self, value):
        """Update ground threshold label"""
        threshold = value / 100.0
        self.ground_threshold_label.setText(f"{threshold:.2f}")
    
    def run_icp_alignment(self):
        """Run ICP alignment in background thread"""
        if self.ref_cloud is None or self.target_cloud is None:
            QMessageBox.warning(self, "Error", "Both reference and target clouds must be loaded")
            return
        
        self.log("Starting ICP alignment...")
        self._start_worker('icp', source=self.target_cloud, target=self.ref_cloud)
    
    def run_ground_removal(self):
        """Run ground removal in background thread"""
        cloud = self.aligned_target if self.aligned_target is not None else self.target_cloud
        
        if cloud is None:
            QMessageBox.warning(self, "Error", "Target cloud must be loaded")
            return
        
        threshold = self.ground_threshold_slider.value() / 100.0
        self.log(f"Starting ground removal (threshold: {threshold:.2f}m)...")
        self._start_worker('ground_removal', pcd=cloud, threshold=threshold)
    
    def run_change_detection(self):
        """Run change detection in background thread"""
        if self.ref_cloud is None or self.aligned_target is None:
            QMessageBox.warning(self, "Error", "Clouds must be aligned first")
            return
        
        self.log("Starting change detection...")
        self._start_worker('change_detection', source=self.aligned_target, target=self.ref_cloud)
    
    def _start_worker(self, task_type: str, **kwargs):
        """Start background worker thread"""
        # Disable buttons
        self.align_btn.setEnabled(False)
        self.remove_ground_btn.setEnabled(False)
        self.change_map_btn.setEnabled(False)
        
        # Show progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Create worker and thread
        self.worker = AnalysisWorker(task_type, **kwargs)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(lambda result: self._on_finished(task_type, result))
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self._cleanup_worker)
        
        # Start thread
        self.worker_thread.start()
    
    def _on_progress(self, percentage: int, message: str):
        """Handle progress updates"""
        self.progress_bar.setValue(percentage)
        self.log(message)
    
    def _on_finished(self, task_type: str, result):
        """Handle task completion"""
        if task_type == 'icp':
            self._handle_icp_result(result)
        elif task_type == 'ground_removal':
            self._handle_ground_removal_result(result)
        elif task_type == 'change_detection':
            self._handle_change_detection_result(result)
    
    def _handle_icp_result(self, result: RegistrationResult):
        """Handle ICP alignment result"""
        self.log(f"ICP Complete: {result}")
        
        # Apply transformation to target
        self.aligned_target = apply_transformation(self.target_cloud, result.transformation)
        
        # Update metrics
        self.icp_metrics_label.setText(
            f"Fitness: {result.fitness:.4f} | Inlier RMSE: {result.inlier_rmse:.4f}m | "
            f"Iterations: {len(result.iteration_log)}"
        )
        
        # Plot convergence
        self._plot_icp_convergence(result.iteration_log)
        
        # Update viewer
        self.cloud_updated.emit('target', self.aligned_target)
        
        # Enable change detection
        self.change_map_btn.setEnabled(True)
        
        # Emit signal for report panel
        self.icp_completed.emit(result.fitness, result.inlier_rmse, len(result.iteration_log))
        
        self.log("✓ Target cloud aligned to reference")
    
    def _handle_ground_removal_result(self, result):
        """Handle ground removal result"""
        ground, non_ground, seg_result = result
        
        original_count = len(self.target_cloud.points)
        stats = get_ground_removal_stats(seg_result, original_count)
        
        self.ground_stats_label.setText(stats)
        self.log(f"Ground Removal Complete: {stats}")
        
        # Update aligned target
        self.aligned_target = non_ground
        
        # Update viewer
        self.cloud_updated.emit('target', non_ground)
        
        # Emit signal for report panel
        threshold = self.ground_threshold_slider.value() / 100.0
        self.ground_removed.emit(threshold, seg_result.num_ground, seg_result.num_non_ground)
        
        self.log("✓ Ground points removed")
    
    def _handle_change_detection_result(self, result):
        """Handle change detection result"""
        change_result, colorized = result
        self.change_result = change_result
        
        # Update stats
        stats = change_result.get_statistics_str()
        summary = get_change_summary(change_result, threshold=0.05)
        
        self.change_stats_label.setText(f"{stats}\n{summary}")
        self.log(f"Change Detection Complete: {stats}")
        
        # Plot histogram
        self._plot_distance_histogram(change_result)
        
        # Update viewer with colorized cloud
        self.cloud_updated.emit('target', colorized)
        
        # Emit signal for clustering panel (pass aligned cloud and distances)
        if self.aligned_target is not None:
            self.change_detected.emit(self.aligned_target, change_result.distances, change_result)
        
        self.log("✓ Change map computed and visualized")
    
    def _on_error(self, error_msg: str):
        """Handle errors"""
        self.log(f"ERROR: {error_msg}")
        QMessageBox.critical(self, "Analysis Error", f"An error occurred:\n{error_msg}")
    
    def _cleanup_worker(self):
        """Clean up worker thread"""
        self.progress_bar.setVisible(False)
        
        # Re-enable buttons
        both_loaded = self.ref_cloud is not None and self.target_cloud is not None
        self.align_btn.setEnabled(both_loaded)
        self.remove_ground_btn.setEnabled(self.target_cloud is not None)
        if self.aligned_target is not None:
            self.change_map_btn.setEnabled(True)
        
        # Clean up thread
        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def _plot_icp_convergence(self, iteration_log):
        """Plot ICP convergence"""
        self.icp_figure.clear()
        ax = self.icp_figure.add_subplot(111)
        
        if iteration_log:
            iterations = [log['iteration'] for log in iteration_log]
            rmse_values = [log['rmse'] for log in iteration_log]
            
            ax.plot(iterations, rmse_values, 'b-', linewidth=2)
            ax.set_xlabel('Iteration')
            ax.set_ylabel('RMSE (m)')
            ax.set_title('ICP Convergence')
            ax.grid(True, alpha=0.3)
        
        self.icp_canvas.draw()
    
    def _plot_distance_histogram(self, change_result):
        """Plot distance histogram"""
        self.hist_figure.clear()
        ax = self.hist_figure.add_subplot(111)
        
        distances = change_result.distances
        signed = change_result.signed
        
        ax.hist(distances, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
        
        mean = np.mean(distances)
        ax.axvline(mean, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean:.3f}m')
        
        if signed:
            ax.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
            ax.set_xlabel('Signed Distance (m)')
        else:
            ax.set_xlabel('Distance (m)')
        
        ax.set_ylabel('Frequency')
        ax.set_title('Change Map Distribution')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        
        self.hist_figure.tight_layout()
        self.hist_canvas.draw()
    
    def log(self, message: str):
        """Add message to log"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
