"""
LiDAR Infrastructure Inspector - Report Generator
PDF report generation with screenshots, plots, and tables
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak
)
from reportlab.lib import colors


class ReportData:
    """Container for report data"""
    
    def __init__(self):
        # File information
        self.ref_filename = None
        self.target_filename = None
        self.ref_point_count = 0
        self.target_point_count = 0
        self.generation_date = datetime.now()
        
        # ICP metrics
        self.icp_fitness = None
        self.icp_rmse = None
        self.icp_iterations = None
        
        # Ground removal
        self.ground_threshold = None
        self.ground_points = None
        self.non_ground_points = None
        
        # Change detection
        self.change_mean = None
        self.change_std = None
        self.change_min = None
        self.change_max = None
        self.change_median = None
        
        # Clustering
        self.clustering_eps = None
        self.clustering_min_samples = None
        self.clustering_threshold = None
        self.num_clusters = None
        self.num_noise = None
        self.cluster_infos = []
        
        # Screenshots and plots
        self.ref_screenshot_path = None
        self.target_screenshot_path = None
        self.histogram_path = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for easy access"""
        return {
            'ref_filename': self.ref_filename,
            'target_filename': self.target_filename,
            'ref_point_count': self.ref_point_count,
            'target_point_count': self.target_point_count,
            'generation_date': self.generation_date.strftime('%Y-%m-%d %H:%M:%S'),
            'icp_fitness': self.icp_fitness,
            'icp_rmse': self.icp_rmse,
            'icp_iterations': self.icp_iterations,
            'ground_threshold': self.ground_threshold,
            'ground_points': self.ground_points,
            'non_ground_points': self.non_ground_points,
            'change_mean': self.change_mean,
            'change_std': self.change_std,
            'change_min': self.change_min,
            'change_max': self.change_max,
            'change_median': self.change_median,
            'clustering_eps': self.clustering_eps,
            'clustering_min_samples': self.clustering_min_samples,
            'clustering_threshold': self.clustering_threshold,
            'num_clusters': self.num_clusters,
            'num_noise': self.num_noise
        }


def generate_preview_text(data: ReportData) -> str:
    """
    Generate markdown-like preview text for report.
    
    Args:
        data: ReportData object
        
    Returns:
        Formatted preview text
    """
    lines = []
    
    lines.append("# LiDAR Infrastructure Analysis Report")
    lines.append("")
    lines.append(f"**Generated:** {data.generation_date.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Files
    lines.append("## Input Files")
    lines.append(f"- **Reference:** {data.ref_filename or 'Not loaded'} ({data.ref_point_count:,} points)")
    lines.append(f"- **Target:** {data.target_filename or 'Not loaded'} ({data.target_point_count:,} points)")
    lines.append("")
    
    # ICP
    if data.icp_fitness is not None:
        lines.append("## ICP Alignment")
        lines.append(f"- **Fitness:** {data.icp_fitness:.4f}")
        lines.append(f"- **Inlier RMSE:** {data.icp_rmse:.4f} m")
        lines.append(f"- **Iterations:** {data.icp_iterations}")
        lines.append("")
    
    # Ground removal
    if data.ground_threshold is not None:
        lines.append("## Ground Removal")
        lines.append(f"- **Threshold:** {data.ground_threshold:.2f} m")
        lines.append(f"- **Ground Points:** {data.ground_points:,}")
        lines.append(f"- **Non-Ground Points:** {data.non_ground_points:,}")
        lines.append("")
    
    # Change detection
    if data.change_mean is not None:
        lines.append("## Change Detection")
        lines.append(f"- **Mean Distance:** {data.change_mean:.3f} m")
        lines.append(f"- **Std Deviation:** {data.change_std:.3f} m")
        lines.append(f"- **Range:** [{data.change_min:.3f}, {data.change_max:.3f}] m")
        lines.append(f"- **Median:** {data.change_median:.3f} m")
        lines.append("")
    
    # Clustering
    if data.num_clusters is not None:
        lines.append("## Clustering")
        lines.append(f"- **Epsilon:** {data.clustering_eps:.2f} m")
        lines.append(f"- **Min Samples:** {data.clustering_min_samples}")
        lines.append(f"- **Change Threshold:** {data.clustering_threshold:.2f} m")
        lines.append(f"- **Clusters Found:** {data.num_clusters}")
        lines.append(f"- **Noise Points:** {data.num_noise:,}")
        lines.append("")
        
        if data.cluster_infos:
            lines.append("### Cluster Details")
            lines.append("")
            lines.append("| ID | Points | Volume (m³) | Centroid (X, Y, Z) |")
            lines.append("|---:|-------:|------------:|:-------------------|")
            
            for info in data.cluster_infos[:20]:  # Limit to top 20
                centroid_str = f"({info.centroid[0]:.1f}, {info.centroid[1]:.1f}, {info.centroid[2]:.1f})"
                lines.append(f"| {info.cluster_id:3d} | {info.num_points:6,} | {info.volume:11.3f} | {centroid_str} |")
            
            if len(data.cluster_infos) > 20:
                lines.append(f"| ... | ... | ... | ({len(data.cluster_infos) - 20} more clusters) |")
    
    return "\n".join(lines)


def generate_pdf_report(data: ReportData, output_path: str):
    """
    Generate PDF report with ReportLab.
    
    Args:
        data: ReportData object
        output_path: Path to save PDF
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("LiDAR Infrastructure Analysis Report", title_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Generated: {data.generation_date.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(PageBreak())
    
    # Input files section
    story.append(Paragraph("Input Files", heading_style))
    file_data = [
        ['Type', 'Filename', 'Points'],
        ['Reference', data.ref_filename or 'N/A', f'{data.ref_point_count:,}'],
        ['Target', data.target_filename or 'N/A', f'{data.target_point_count:,}']
    ]
    file_table = Table(file_data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
    file_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(file_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ICP metrics
    if data.icp_fitness is not None:
        story.append(Paragraph("ICP Alignment", heading_style))
        icp_data = [
            ['Metric', 'Value'],
            ['Fitness', f'{data.icp_fitness:.4f}'],
            ['Inlier RMSE', f'{data.icp_rmse:.4f} m'],
            ['Iterations', str(data.icp_iterations)]
        ]
        icp_table = Table(icp_data, colWidths=[2*inch, 2*inch])
        icp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
        ]))
        story.append(icp_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Screenshots
    if data.ref_screenshot_path and data.target_screenshot_path:
        if os.path.exists(data.ref_screenshot_path) and os.path.exists(data.target_screenshot_path):
            story.append(Paragraph("Point Cloud Comparison", heading_style))
            
            # Side-by-side images
            img_width = 3*inch
            img_height = 2.5*inch
            
            screenshot_data = [
                [
                    Image(data.ref_screenshot_path, width=img_width, height=img_height),
                    Image(data.target_screenshot_path, width=img_width, height=img_height)
                ],
                ['Reference', 'Target (Processed)']
            ]
            screenshot_table = Table(screenshot_data, colWidths=[3.25*inch, 3.25*inch])
            screenshot_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold')
            ]))
            story.append(screenshot_table)
            story.append(Spacer(1, 0.3*inch))
    
    # Change detection
    if data.change_mean is not None:
        story.append(Paragraph("Change Detection", heading_style))
        change_data = [
            ['Statistic', 'Value (m)'],
            ['Mean Distance', f'{data.change_mean:.3f}'],
            ['Std Deviation', f'{data.change_std:.3f}'],
            ['Minimum', f'{data.change_min:.3f}'],
            ['Maximum', f'{data.change_max:.3f}'],
            ['Median', f'{data.change_median:.3f}']
        ]
        change_table = Table(change_data, colWidths=[2*inch, 2*inch])
        change_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
        ]))
        story.append(change_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Histogram
        if data.histogram_path and os.path.exists(data.histogram_path):
            story.append(Paragraph("Distance Distribution", heading_style))
            story.append(Image(data.histogram_path, width=5*inch, height=3*inch))
            story.append(Spacer(1, 0.3*inch))
    
    # Clustering
    if data.num_clusters is not None:
        story.append(PageBreak())
        story.append(Paragraph("Clustering Results", heading_style))
        
        cluster_summary_data = [
            ['Parameter', 'Value'],
            ['Epsilon', f'{data.clustering_eps:.2f} m'],
            ['Min Samples', str(data.clustering_min_samples)],
            ['Change Threshold', f'{data.clustering_threshold:.2f} m'],
            ['Clusters Found', str(data.num_clusters)],
            ['Noise Points', f'{data.num_noise:,}']
        ]
        cluster_summary_table = Table(cluster_summary_data, colWidths=[2*inch, 2*inch])
        cluster_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
        ]))
        story.append(cluster_summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Cluster details table
        if data.cluster_infos:
            story.append(Paragraph("Cluster Details", heading_style))
            
            cluster_data = [['ID', 'Points', 'Volume (m³)', 'Centroid (X, Y, Z)']]
            
            for info in data.cluster_infos[:20]:  # Limit to top 20
                centroid_str = f"({info.centroid[0]:.1f}, {info.centroid[1]:.1f}, {info.centroid[2]:.1f})"
                cluster_data.append([
                    str(info.cluster_id),
                    f'{info.num_points:,}',
                    f'{info.volume:.3f}',
                    centroid_str
                ])
            
            cluster_table = Table(cluster_data, colWidths=[0.5*inch, 1*inch, 1.5*inch, 3.5*inch])
            cluster_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (2, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige)
            ]))
            story.append(cluster_table)
            
            if len(data.cluster_infos) > 20:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(f"... and {len(data.cluster_infos) - 20} more clusters", styles['Italic']))
    
    # Build PDF
    doc.build(story)


def save_histogram_plot(distances: np.ndarray, output_path: str, signed: bool = False):
    """
    Save histogram plot to file.
    
    Args:
        distances: Distance array
        output_path: Path to save image
        signed: Whether distances are signed
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.hist(distances, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    
    mean = np.mean(distances)
    ax.axvline(mean, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean:.3f}m')
    
    if signed:
        ax.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        ax.set_xlabel('Signed Distance (m)', fontsize=12)
    else:
        ax.set_xlabel('Distance (m)', fontsize=12)
    
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Change Map Distribution', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
