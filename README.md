# LiDAR Infrastructure Inspector (CivilScan-3D)

**Complete Desktop Application** - Open-source tool for civil engineers to analyze LiDAR point clouds and detect terrain defects.

## 🎯 Features (All Phases Complete)

### Phase 1: Dual Viewport Viewer
- **Dual Viewport**: Side-by-side comparison of Reference and Target point clouds
- **Multiple Formats**: Supports `.ply`, `.pcd`, `.xyz`, `.txt`, `.las`, `.laz`
- **Drag & Drop**: Drop files directly onto viewports
- **Interactive Navigation**: Orbit, pan, and zoom controls

### Phase 2: Analysis Pipeline
- **ICP Alignment**: Automatic registration with convergence plots
- **Ground Removal**: RANSAC-based ground plane segmentation
- **Change Detection**: Signed distance computation with histogram visualization
- **Color Mapping**: Blue (erosion) to Red (deposition) visualization

### Phase 3: Real-Time Clustering
- **DBSCAN Clustering**: Interactive parameter tuning with debounced sliders
- **Cluster Inspection**: Click to highlight, view statistics, isolate clusters
- **Export Clusters**: Save individual clusters as PLY files
- **Volume Estimation**: Bounding box volume proxy for each cluster

### Phase 4: Report Generation & Packaging
- **PDF Reports**: Automated report generation with screenshots and plots
- **Preview**: Markdown-like preview before generating PDF
- **Standalone Builds**: PyInstaller support for Windows, macOS, Linux
- **Screenshots**: Automatic capture of analysis results

## 📋 Requirements

- Python 3.10 or higher
- Works on Windows, macOS, and Linux

## 🚀 Installation

### 1. Clone or Download

```bash
cd "/Users/parimal/Desktop/PYTHON/PYTHONPRACTICE/PROJECTS/Infrastructure Inspector"
```

### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 🎮 Usage

### Quick Start

```bash
python main.py
```

### Demo Workflow

**1. Generate Test Data**
```bash
python create_test_data.py
```
This creates `test_reference.ply` (baseline terrain) and `test_target.ply` (with simulated erosion/deposition).

**2. Load Point Clouds**
- Click **"Load Reference"** → select `test_reference.ply`
- Click **"Load Target"** → select `test_target.ply`
- Or drag-and-drop files onto viewports

**3. Run Analysis Pipeline** (Analysis Tab)
- Click **"Align Scans (ICP)"** → wait for alignment
  - View convergence plot
  - Check fitness (~0.7-0.9) and RMSE
- Adjust **Ground Threshold** slider (default: 0.15m)
- Click **"Remove Ground"** → removes ground plane
- Click **"Compute Change Map"** → generates signed distance map
  - View histogram of changes
  - Blue = erosion, Red = deposition

**4. Cluster Defects** (Clustering Tab)
- Adjust sliders:
  - **Epsilon**: 0.30m (cluster radius)
  - **Min Samples**: 20 (minimum points per cluster)
  - **Change Threshold**: 0.10m (filter small changes)
- Wait 300ms → clustering runs automatically
- View cluster list (ID, points, volume)
- Click cluster → **"Highlight Selected"** → inspect in red
- **"Export All Clusters"** → save as separate PLY files

**5. Generate Report** (Report Tab)
- Review preview (shows all analysis results)
- Click **"Generate PDF Report"**
- Select output location
- PDF includes:
  - Title page with metadata
  - Side-by-side screenshots
  - Change detection histogram
  - Cluster statistics table

### Navigation

- **Rotate**: Left mouse button + drag
- **Pan**: Right mouse button + drag (or Shift + left mouse)
- **Zoom**: Mouse wheel

### Supported Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PLY | `.ply` | Native Open3D support |
| PCD | `.pcd` | Native Open3D support |
| XYZ | `.xyz`, `.txt` | Space/tab separated X Y Z [R G B] |
| LAS/LAZ | `.las`, `.laz` | Requires `laspy` package |

## 📁 Project Structure

```
Infrastructure Inspector/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── BUILD.md                     # Build instructions for standalone executables
├── QUICKSTART.md                # Quick start guide
├── lidar_inspector.spec         # PyInstaller spec file
├── create_test_data.py          # Test data generator
├── screenshots/                 # Demo screenshots
├── core/                        # Core analysis modules
│   ├── loader.py                # Point cloud loading
│   ├── registration.py          # ICP alignment
│   ├── segmentation.py          # Ground removal
│   ├── change_detection.py      # Distance computation
│   ├── clustering.py            # DBSCAN clustering
│   └── reporter.py              # PDF report generation
└── gui/                         # GUI modules
    ├── main_window.py           # Main application window
    ├── viewer_widget.py         # 3D viewer widget
    ├── analysis_panel.py        # Analysis controls
    ├── clustering_panel.py      # Clustering controls
    └── report_panel.py          # Report generation
```

## 🧪 Testing

### Full Pipeline Test

```bash
# 1. Generate test data
python create_test_data.py

# 2. Run application
python main.py

# 3. Follow demo workflow above
```

**Expected Results:**
- ICP fitness: 0.7-0.9
- Change detection: Mean ~0.1m, bimodal distribution
- Clustering: 6-10 clusters detected
- PDF report: Generated with all sections

## 🔧 Troubleshooting

### Open3D Visualization Issues

The app uses Open3D for 3D visualization. If embedding fails on your platform:
- **Fallback Mode**: The app will show a placeholder and provide a "View in External Window" button
- **External Viewer**: Click the button to open point clouds in a separate Open3D window

### LAS/LAZ Files Won't Load

```bash
pip install laspy[lazrs]
```

If installation fails, you can still use other formats (.ply, .pcd, .xyz, .txt).

### Qt Platform Plugin Error

On Linux, you may need:
```bash
sudo apt-get install python3-pyqt5
```

On macOS with M1/M2:
```bash
pip install --upgrade PyQt5
```

### PDF Generation Fails

Ensure reportlab is installed:
```bash
pip install reportlab
```

## 📦 Building Standalone Executables

See [BUILD.md](BUILD.md) for detailed instructions on creating standalone executables for:
- **Windows** (.exe)
- **macOS** (.app)
- **Linux** (binary)

Quick build:
```bash
pip install pyinstaller
pyinstaller lidar_inspector.spec
```

## 📸 Screenshots

See `screenshots/` folder for demo workflow images.

## 📝 Acceptance Criteria (All Phases)

### Phase 1: Dual Viewport
- [x] App opens without error
- [x] Load Reference/Target buttons work
- [x] Drag & drop functional
- [x] Navigation (orbit/pan/zoom) works

### Phase 2: Analysis Pipeline
- [x] ICP alignment with convergence plot
- [x] Ground removal with threshold slider
- [x] Change detection with histogram
- [x] Signed distance colorization

### Phase 3: Clustering
- [x] DBSCAN with debounced sliders
- [x] Cluster list with statistics
- [x] Highlight/isolate clusters
- [x] Export clusters as PLY

### Phase 4: Reporting
- [x] PDF report generation
- [x] Screenshots and plots included
- [x] Preview before generation
- [x] Build instructions for all platforms

## 🚧 Future Enhancements

- Convex hull volume calculation
- Multi-temporal analysis (3+ scans)
- Custom colormap selection
- Batch processing mode
- Cloud-based storage integration

## 📄 License

Open-source project for civil engineering applications.

## 🤝 Contributing

All phases complete! Contributions for enhancements welcome.

---

**Version**: 4.0.0 (All Phases Complete)  
**Last Updated**: January 2026  
**Status**: Production Ready
