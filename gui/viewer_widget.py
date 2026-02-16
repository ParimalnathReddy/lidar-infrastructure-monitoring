"""
LiDAR Infrastructure Inspector - 3D Viewer Widget
Displays point clouds using Open3D with fallback options
"""
import sys
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import open3d as o3d

# Optional visualization fallbacks
try:
    import pyvista as pv
except Exception:  # pragma: no cover - optional dependency
    pv = None

try:
    import vedo
except Exception:  # pragma: no cover - optional dependency
    vedo = None


class ViewerWidget(QWidget):
    """
    3D point cloud viewer widget with drag-and-drop support.
    Uses Open3D's GUI for embedded visualization.
    """
    
    file_dropped = pyqtSignal(str)  # Signal emitted when file is dropped
    
    def __init__(self, title: str = "Viewer", parent=None):
        super().__init__(parent)
        self.title = title
        self.point_cloud = None
        self.use_fallback = False
        
        self.setAcceptDrops(True)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: white;
                padding: 8px;
                font-weight: bold;
                font-size: 12pt;
            }
        """)
        layout.addWidget(self.title_label)
        
        # Try to create Open3D visualization widget
        try:
            self.o3d_widget = self._create_o3d_widget()
            layout.addWidget(self.o3d_widget, 1)
            self.use_fallback = False
        except Exception as e:
            print(f"Warning: Could not create embedded Open3D widget: {e}")
            print("Using fallback mode with external viewer")
            self.use_fallback = True
            
            # Fallback: show placeholder with button
            self.placeholder = QLabel("Drop point cloud here\nor use Load button")
            self.placeholder.setAlignment(Qt.AlignCenter)
            self.placeholder.setStyleSheet("""
                QLabel {
                    background-color: #34495e;
                    color: #95a5a6;
                    font-size: 14pt;
                    border: 2px dashed #7f8c8d;
                }
            """)
            layout.addWidget(self.placeholder, 1)
            
            self.view_button = QPushButton("Open in External Viewer")
            self.view_button.clicked.connect(self._view_external)
            self.view_button.setEnabled(False)
            layout.addWidget(self.view_button)
        
        self.setLayout(layout)
    
    def _create_o3d_widget(self):
        """Create Open3D visualization widget (embedded mode)"""
        # NOTE: The embedded Open3D/Qt viewer was never fully implemented and
        # results in a blank panel. Force fallback mode so the external window
        # (Open3D / PyVista / vedo) is used instead.
        raise NotImplementedError("Embedded Open3D widget not implemented")
    
    def load_point_cloud(self, pcd: o3d.geometry.PointCloud, filename: str = ""):
        """
        Load and display a point cloud.
        
        Args:
            pcd: Open3D PointCloud object
            filename: Optional filename for display
        """
        self.point_cloud = pcd
        
        if filename:
            self.title_label.setText(f"{self.title}: {filename}")
        
        if self.use_fallback:
            # Enable external viewer button
            if hasattr(self, 'view_button'):
                self.view_button.setEnabled(True)
                self.placeholder.setText(f"Loaded: {filename}\n{len(pcd.points):,} points\nClick button to view")
        else:
            # Render in embedded widget
            self._render_point_cloud()
    
    def _render_point_cloud(self):
        """Render point cloud in embedded widget"""
        if self.point_cloud is None:
            return
        
        # For embedded rendering, we'll use a simplified approach
        # In production, this would use Open3D's rendering engine properly
        # For now, update the placeholder to show it's loaded
        if hasattr(self, 'placeholder'):
            points = np.asarray(self.point_cloud.points)
            self.placeholder.setText(
                f"Point Cloud Loaded\n"
                f"{len(points):,} points\n"
                f"(Embedded view in development)"
            )
    
    def _view_external(self):
        """Open point cloud in external Open3D viewer"""
        if self.point_cloud is not None:
            # Prefer PyVista > vedo > Open3D
            if pv is not None:
                try:
                    pts = np.asarray(self.point_cloud.points)
                    poly = pv.PolyData(pts)
                    if self.point_cloud.has_colors():
                        colors = (np.asarray(self.point_cloud.colors) * 255).astype(np.uint8)
                        poly['colors'] = colors
                        cmap_arg = None
                        scalars = 'colors'
                    else:
                        cmap_arg = "viridis"
                        scalars = None
                    plotter = pv.Plotter(window_size=(1000, 800), title=self.title)
                    plotter.add_points(poly, scalars=scalars, rgb=self.point_cloud.has_colors(),
                                       render_points_as_spheres=False, point_size=2, cmap=cmap_arg)
                    plotter.show()
                    return
                except Exception as e:  # fall through to next backend
                    print(f"PyVista viewer failed: {e}")
            if vedo is not None:
                try:
                    pts = np.asarray(self.point_cloud.points)
                    p = vedo.Points(pts, r=2)
                    if self.point_cloud.has_colors():
                        colors = (np.asarray(self.point_cloud.colors) * 255).astype(np.uint8)
                        p.cmap(None).pointColors(colors)
                    vedo.show(p, title=self.title, size=(1000, 800))
                    return
                except Exception as e:
                    print(f"vedo viewer failed: {e}")
            # Fallback to Open3D
            try:
                o3d.visualization.draw_geometries(
                    [self.point_cloud],
                    window_name=f"{self.title}",
                    width=1000,
                    height=800
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Visualization Error",
                    f"Could not open external viewer: {str(e)}"
                )
    
    def clear(self):
        """Clear the current point cloud"""
        self.point_cloud = None
        self.title_label.setText(self.title)
        
        if self.use_fallback and hasattr(self, 'placeholder'):
            self.placeholder.setText("Drop point cloud here\nor use Load button")
            self.view_button.setEnabled(False)
    
    # Drag and drop support
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                filepath = urls[0].toLocalFile()
                ext = filepath.split('.')[-1].lower()
                if ext in ['ply', 'pcd', 'xyz', 'txt', 'las', 'laz']:
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move event"""
        event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            self.file_dropped.emit(filepath)
            event.acceptProposedAction()
