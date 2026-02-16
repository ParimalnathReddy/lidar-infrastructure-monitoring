# Screenshots

This folder contains demonstration screenshots and example outputs from the LiDAR Infrastructure Inspector application.

## Workflow Screenshots

To generate workflow screenshots:

1. **Load Data:**
   - Load `test_reference.ply` and `test_target.ply`
   - Capture: Dual viewport with both clouds loaded

2. **ICP Alignment:**
   - Run ICP alignment
   - Capture: Convergence plot and aligned clouds

3. **Ground Removal:**
   - Apply ground removal
   - Capture: Before/after comparison

4. **Change Detection:**
   - Compute change map
   - Capture: Colorized change map and histogram

5. **Clustering:**
   - Run DBSCAN clustering
   - Capture: Cluster visualization and cluster list

6. **Report Generation:**
   - Generate PDF report
   - Capture: Report preview and generated PDF

## Screenshot Naming Convention

- `01_dual_viewport.png` - Initial dual viewport
- `02_icp_alignment.png` - ICP convergence plot
- `03_ground_removal.png` - Ground removal result
- `04_change_detection.png` - Change map visualization
- `05_clustering.png` - Cluster visualization
- `06_report_preview.png` - Report preview
- `07_pdf_report.png` - Generated PDF report

## Example Outputs

Place example outputs here:
- Sample PDF reports
- Exported cluster PLY files
- Analysis results

## Usage in Documentation

These screenshots are referenced in:
- `README.md` - Main documentation
- `QUICKSTART.md` - Quick start guide
- `walkthrough.md` - Detailed walkthrough

## Capturing Screenshots

**Method 1: Manual Capture**
- macOS: `Cmd + Shift + 4`
- Windows: `Win + Shift + S`
- Linux: `gnome-screenshot -a`

**Method 2: Programmatic Capture**
- Use `QWidget.grab()` in PyQt5
- Save with `QPixmap.save()`

**Method 3: Report Panel**
- The report panel automatically captures viewer screenshots
- Check temp directory for auto-generated screenshots
