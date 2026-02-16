#!/usr/bin/env python3
"""
LiDAR Infrastructure Inspector
Phase 1: Dual Viewport Viewer

Entry point for the application.
"""
import os
import sys

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui.main_window import MainWindow

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = MainWindow()
    window.showMaximized()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
