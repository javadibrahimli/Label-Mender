"""Main entry point for Label Mender application."""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Add parent directory to path to allow imports
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui import MainWindow


def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icon', 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
