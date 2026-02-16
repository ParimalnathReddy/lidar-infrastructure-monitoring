# Building LiDAR Infrastructure Inspector

This guide provides instructions for building standalone executables of the LiDAR Infrastructure Inspector application.

## Prerequisites

1. **Python 3.10+** installed
2. **All dependencies** installed: `pip install -r requirements.txt`
3. **PyInstaller** installed: `pip install pyinstaller`

## Platform-Specific Build Instructions

### Windows Build

**Requirements:**
- Windows 10/11
- Visual C++ Redistributable (usually pre-installed)

**Build Command:**
```bash
# Navigate to project directory
cd "Infrastructure Inspector"

# Build using spec file
pyinstaller lidar_inspector.spec

# Or use direct command
pyinstaller --name="LiDAR_Inspector" ^
            --windowed ^
            --onedir ^
            --add-data="venv/Lib/site-packages/open3d/resources;open3d/resources" ^
            --hidden-import=numpy ^
            --hidden-import=open3d ^
            --hidden-import=PyQt5 ^
            --hidden-import=laspy ^
            --hidden-import=matplotlib ^
            --hidden-import=sklearn ^
            --hidden-import=reportlab ^
            main.py
```

**Output:**
- Executable: `dist/LiDAR_Inspector/LiDAR_Inspector.exe`
- Distribute entire `dist/LiDAR_Inspector/` folder

**Testing:**
```bash
cd dist/LiDAR_Inspector
LiDAR_Inspector.exe
```

---

### macOS Build

**Requirements:**
- macOS 10.15+ (Catalina or later)
- Xcode Command Line Tools: `xcode-select --install`

**Build Command:**
```bash
# Navigate to project directory
cd "Infrastructure Inspector"

# Build using spec file
pyinstaller lidar_inspector.spec

# Or use direct command
pyinstaller --name="LiDAR_Inspector" \
            --windowed \
            --onedir \
            --add-data="venv/lib/python*/site-packages/open3d/resources:open3d/resources" \
            --hidden-import=numpy \
            --hidden-import=open3d \
            --hidden-import=PyQt5 \
            --hidden-import=laspy \
            --hidden-import=matplotlib \
            --hidden-import=sklearn \
            --hidden-import=reportlab \
            main.py
```

**Output:**
- App Bundle: `dist/LiDAR_Inspector.app`
- Distribute the `.app` bundle

**Testing:**
```bash
open dist/LiDAR_Inspector.app
```

**Code Signing (Optional):**
```bash
# Sign the app (requires Apple Developer account)
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/LiDAR_Inspector.app
```

---

### Linux Build

**Requirements:**
- Ubuntu 20.04+ / Debian 11+ / Fedora 35+
- Python 3.10+ with tkinter: `sudo apt install python3-tk` (Ubuntu/Debian)

**Build Command:**
```bash
# Navigate to project directory
cd "Infrastructure Inspector"

# Build using spec file
pyinstaller lidar_inspector.spec

# Or use direct command
pyinstaller --name="LiDAR_Inspector" \
            --windowed \
            --onedir \
            --add-data="venv/lib/python*/site-packages/open3d/resources:open3d/resources" \
            --hidden-import=numpy \
            --hidden-import=open3d \
            --hidden-import=PyQt5 \
            --hidden-import=laspy \
            --hidden-import=matplotlib \
            --hidden-import=sklearn \
            --hidden-import=reportlab \
            main.py
```

**Output:**
- Executable: `dist/LiDAR_Inspector/LiDAR_Inspector`
- Distribute entire `dist/LiDAR_Inspector/` folder

**Testing:**
```bash
cd dist/LiDAR_Inspector
./LiDAR_Inspector
```

**Create Desktop Entry (Optional):**
```bash
cat > ~/.local/share/applications/lidar-inspector.desktop << EOF
[Desktop Entry]
Name=LiDAR Inspector
Exec=/path/to/dist/LiDAR_Inspector/LiDAR_Inspector
Icon=/path/to/icon.png
Type=Application
Categories=Science;Engineering;
EOF
```

---

## Build Options Explained

| Option | Description |
|--------|-------------|
| `--name` | Name of the executable |
| `--windowed` | No console window (GUI only) |
| `--onedir` | Create a folder with executable and dependencies |
| `--onefile` | Create a single executable (slower startup) |
| `--add-data` | Include non-Python files (Open3D resources) |
| `--hidden-import` | Force include modules not auto-detected |

**Recommendation:** Use `--onedir` for faster startup and easier debugging.

---

## Troubleshooting

### Issue: "Failed to execute script main"

**Solution:** Run with console to see errors:
```bash
# Remove --windowed flag or set console=True in spec file
pyinstaller lidar_inspector.spec --console
```

### Issue: Open3D rendering errors

**Solution:** Ensure Open3D resources are included:
```bash
# Verify resources are in dist folder
ls dist/LiDAR_Inspector/open3d/resources
```

### Issue: Missing DLLs (Windows)

**Solution:** Install Visual C++ Redistributable:
- Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Issue: "Module not found" errors

**Solution:** Add missing modules to `hiddenimports` in spec file:
```python
hiddenimports=[
    'numpy',
    'open3d',
    # Add missing module here
],
```

### Issue: Large executable size

**Solution:** Use UPX compression (already enabled in spec file):
```bash
# Install UPX
# Windows: Download from https://upx.github.io/
# macOS: brew install upx
# Linux: sudo apt install upx-ucl
```

---

## Docker Deployment (NOT RECOMMENDED)

> **⚠️ WARNING:** Docker deployment is **not recommended** for this application due to Open3D GUI requirements.

**Why Docker doesn't work well:**
1. **Open3D requires OpenGL** for 3D rendering
2. **X11 forwarding** is complex and slow
3. **No GPU acceleration** in most Docker setups
4. **PyQt5 GUI** needs display server

**If you must use Docker (headless mode only):**
- Remove all GUI components
- Use Open3D in headless mode
- Run as CLI tool only
- No interactive 3D visualization

**Honest recommendation:** Use native builds (Windows/macOS/Linux) for best user experience.

---

## Distribution Checklist

Before distributing your build:

- [ ] Test on clean system (no Python installed)
- [ ] Verify all features work (load, align, cluster, report)
- [ ] Check PDF generation works
- [ ] Test with sample data files
- [ ] Include README and QUICKSTART in distribution
- [ ] Provide sample `.ply` files for testing
- [ ] Document system requirements
- [ ] Test on minimum supported OS version

---

## Build Artifacts

After successful build, you'll have:

```
dist/
└── LiDAR_Inspector/
    ├── LiDAR_Inspector(.exe)    # Main executable
    ├── _internal/                # Dependencies (Windows/Linux)
    │   ├── open3d/
    │   ├── PyQt5/
    │   ├── numpy/
    │   └── ...
    └── (various .dylib/.so/.dll files)
```

**Distribution size:** ~300-500 MB (includes all dependencies)

---

## Advanced: Single-File Executable

For simpler distribution (slower startup):

```bash
pyinstaller --name="LiDAR_Inspector" \
            --windowed \
            --onefile \
            --add-data="..." \
            main.py
```

**Trade-offs:**
- ✅ Single file distribution
- ✅ Easier to share
- ❌ Slower startup (extracts to temp)
- ❌ Larger file size
- ❌ Antivirus may flag

---

## Support

For build issues:
1. Check PyInstaller documentation: https://pyinstaller.org/
2. Verify Python version compatibility
3. Test in virtual environment first
4. Check Open3D compatibility: http://www.open3d.org/

---

**Last Updated:** 2026-01-30  
**PyInstaller Version:** 5.0+  
**Python Version:** 3.10+
