# Infrastructure Inspector

A desktop application for civil engineers to analyze LiDAR point clouds and detect terrain changes like erosion or deposition.

## Key Features

- **Side-by-Side Viewing**: Compare reference and target point clouds in dual viewports.
- **Automated Alignment**: Align scans using ICP with real-time feedback.
- **Terrain Analysis**: Remove ground planes and compute signed distance maps to see exactly what changed.
- **Defect Clustering**: Group surface changes into clusters to estimate volumes and inspect specific areas.
- **Reporting**: Generate PDF reports with screenshots, histograms, and statistics.

## Getting Started

### Requirements
- Python 3.10+
- Works on Windows, macOS, and Linux.

### Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/ParimalnathReddy/lidar-infrastructure-monitoring.git
   cd lidar-infrastructure-monitoring
   ```

2. **Set up a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

Start the main script:
```bash
python main.py
```

If you want to try it out with test data first, run:
```bash
python create_test_data.py
```
This generates `test_reference.ply` and `test_target.ply` which you can load into the app.

## How to use it

1. **Load your data**: Drag and drop your `.ply` or `.pcd` files into the left and right viewers.
2. **Align the scans**: Go to the **Analysis** tab and hit "Align Scans". This makes sure your two point clouds are perfectly lined up.
3. **Clean up**: Use "Remove Ground" to filter out the flat terrain so you can focus on the defects.
4. **Find changes**: Click "Compute Change Map". The results are color-coded: blue for where the ground has dropped (erosion) and red for where it's piled up (deposition).
5. **Analyze clusters**: In the **Clustering** tab, the app automatically groups these changes. You can click on specific clusters to see their volume and export them if needed.
6. **Save a report**: Once you're happy with the results, head to the **Report** tab to preview and export a PDF.

## Project Layout

- `core/`: All the math and processing logic (alignment, clustering, etc.).
- `gui/`: Interface code (windows, panels, and 3D widgets).
- `main.py`: The main entry point for the app.
- `create_test_data.py`: A script for generating some sample data to play with.

## Troubleshooting

- **Graphics Issues**: On some systems, the 3D viewers might not embed correctly. If this happens, use the "View in External Window" button.
- **LAS/LAZ files**: If you need to load LAS files, make sure you have `laspy` installed (`pip install laspy[lazrs]`).
- **Linux users**: You might need to install `python3-pyqt5` via your package manager if you run into UI errors.

## License
Open-source tool for civil engineering.
