# Quick Start Guide - LiDAR Infrastructure Inspector

## Installation (One-time setup)

```bash
cd "/Users/parimal/Desktop/PYTHON/PYTHONPRACTICE/PROJECTS/Infrastructure Inspector"
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

## Loading Point Clouds

### Method 1: Buttons
1. Click **"Load Reference"** → select your reference point cloud
2. Click **"Load Target"** → select your target point cloud

### Method 2: Drag & Drop
- Drag file onto **left viewport** = Reference
- Drag file onto **right viewport** = Target

## Supported File Formats

- `.ply` - Polygon File Format
- `.pcd` - Point Cloud Data
- `.xyz` / `.txt` - ASCII XYZ format
- `.las` / `.laz` - LAS format (requires laspy)

## Navigation Controls

- **Rotate**: Left mouse button + drag
- **Pan**: Right mouse button + drag
- **Zoom**: Mouse wheel

## Testing with Sample Data

```bash
# Generate test clouds
python create_test_data.py

# Then load in the app:
# - test_reference.ply (left)
# - test_target.ply (right)
```

## Troubleshooting

**Visualization not working?**
- Click "View in External Window" button
- Point cloud opens in separate Open3D viewer

**LAS/LAZ files won't load?**
```bash
pip install laspy[lazrs]
```

## What's Next?

Phase 1 provides the foundation. Future phases will add:
- Change detection
- DBSCAN clustering
- PDF reports
