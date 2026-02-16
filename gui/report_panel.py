"""
LiDAR Infrastructure Inspector - Report Panel
GUI for report preview and PDF generation
"""
import os
import tempfile
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QTextEdit, QFileDialog, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPixmap
import open3d as o3d

from core.reporter import ReportData, generate_preview_text, generate_pdf_report, save_histogram_plot


class ReportGeneratorWorker(QObject):
    """Worker for generating PDF report in background"""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, report_data: ReportData, output_path: str):
        super().__init__()
        self.report_data = report_data
        self.output_path = output_path
    
    def run(self):
        """Generate PDF report"""
        try:
            self.progress.emit("Generating PDF report...")
            generate_pdf_report(self.report_data, self.output_path)
            self.progress.emit("PDF report generated successfully")
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class ReportPanel(QWidget):
    """Report panel with preview and PDF generation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.report_data = ReportData()
        self.temp_dir = tempfile.mkdtemp(prefix='lidar_report_')
        
        self.worker_thread = None
        self.worker = None
        
        self.init_ui()
        self.update_preview()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Preview section
        preview_group = self._create_preview_section()
        layout.addWidget(preview_group, 1)
        
        # Generate button
        self.generate_btn = QPushButton("Generate PDF Report")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                padding: 12px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_pdf)
        self.generate_btn.setEnabled(False)
        layout.addWidget(self.generate_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def _create_preview_section(self) -> QGroupBox:
        """Create preview text area"""
        group = QGroupBox("Report Preview")
        layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.preview_text)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Preview")
        refresh_btn.clicked.connect(self.update_preview)
        layout.addWidget(refresh_btn)
        
        group.setLayout(layout)
        return group
    
    def set_file_info(self, ref_filename: str, target_filename: str,
                     ref_count: int, target_count: int):
        """Set file information"""
        self.report_data.ref_filename = ref_filename
        self.report_data.target_filename = target_filename
        self.report_data.ref_point_count = ref_count
        self.report_data.target_point_count = target_count
        self.update_preview()
        self._check_ready()
    
    def set_icp_results(self, fitness: float, rmse: float, iterations: int):
        """Set ICP results"""
        self.report_data.icp_fitness = fitness
        self.report_data.icp_rmse = rmse
        self.report_data.icp_iterations = iterations
        self.update_preview()
        self._check_ready()
    
    def set_ground_removal_results(self, threshold: float, ground_points: int, non_ground_points: int):
        """Set ground removal results"""
        self.report_data.ground_threshold = threshold
        self.report_data.ground_points = ground_points
        self.report_data.non_ground_points = non_ground_points
        self.update_preview()
        self._check_ready()
    
    def set_change_detection_results(self, distances, signed: bool):
        """Set change detection results"""
        import numpy as np
        
        self.report_data.change_mean = float(np.mean(distances))
        self.report_data.change_std = float(np.std(distances))
        self.report_data.change_min = float(np.min(distances))
        self.report_data.change_max = float(np.max(distances))
        self.report_data.change_median = float(np.median(distances))
        
        # Save histogram
        histogram_path = os.path.join(self.temp_dir, 'histogram.png')
        save_histogram_plot(distances, histogram_path, signed)
        self.report_data.histogram_path = histogram_path
        
        self.update_preview()
        self._check_ready()
    
    def set_clustering_results(self, eps: float, min_samples: int, threshold: float,
                              num_clusters: int, num_noise: int, cluster_infos: list):
        """Set clustering results"""
        self.report_data.clustering_eps = eps
        self.report_data.clustering_min_samples = min_samples
        self.report_data.clustering_threshold = threshold
        self.report_data.num_clusters = num_clusters
        self.report_data.num_noise = num_noise
        self.report_data.cluster_infos = cluster_infos
        self.update_preview()
        self._check_ready()
    
    def set_screenshots(self, ref_pixmap: QPixmap, target_pixmap: QPixmap):
        """Set viewer screenshots"""
        # Save pixmaps to temp files
        ref_path = os.path.join(self.temp_dir, 'ref_screenshot.png')
        target_path = os.path.join(self.temp_dir, 'target_screenshot.png')
        
        ref_pixmap.save(ref_path)
        target_pixmap.save(target_path)
        
        self.report_data.ref_screenshot_path = ref_path
        self.report_data.target_screenshot_path = target_path
        
        self._check_ready()
    
    def update_preview(self):
        """Update preview text"""
        preview = generate_preview_text(self.report_data)
        self.preview_text.setPlainText(preview)
    
    def _check_ready(self):
        """Check if report is ready to generate"""
        # At minimum, need file info
        ready = (self.report_data.ref_filename is not None and
                self.report_data.target_filename is not None)
        
        self.generate_btn.setEnabled(ready)
    
    def generate_pdf(self):
        """Generate PDF report"""
        # Select output file
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Report",
            "lidar_analysis_report.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not output_path:
            return
        
        # Disable button
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # Create worker
        self.worker = ReportGeneratorWorker(self.report_data, output_path)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self._cleanup_worker)
        
        # Start thread
        self.worker_thread.start()
    
    def _on_progress(self, message: str):
        """Handle progress updates"""
        pass  # Progress bar is indeterminate
    
    def _on_finished(self, output_path: str):
        """Handle PDF generation completion"""
        QMessageBox.information(
            self,
            "Report Generated",
            f"PDF report successfully generated:\n{output_path}"
        )
    
    def _on_error(self, error_msg: str):
        """Handle errors"""
        QMessageBox.critical(
            self,
            "Report Generation Error",
            f"Failed to generate PDF report:\n{error_msg}"
        )
    
    def _cleanup_worker(self):
        """Clean up worker thread"""
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        
        if self.worker_thread:
            self.worker_thread.deleteLater()
            self.worker_thread = None
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def capture_screenshots_from_viewers(self, ref_viewer, target_viewer):
        """
        Capture screenshots from viewer widgets.
        
        Args:
            ref_viewer: Reference viewer widget
            target_viewer: Target viewer widget
        """
        try:
            # Capture widget as pixmap
            ref_pixmap = ref_viewer.grab()
            target_pixmap = target_viewer.grab()
            
            self.set_screenshots(ref_pixmap, target_pixmap)
            
        except Exception as e:
            print(f"Screenshot capture failed: {e}")
