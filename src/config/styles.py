"""Application stylesheet definitions - VS Code inspired theme."""

from .constants import COLORS


STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLORS['background']};
    }}
    
    QWidget {{
        font-family: 'Segoe UI', sans-serif;
        font-size: 11px;
    }}
    
    QGroupBox {{
        font-weight: 600;
        font-size: 11px;
        color: {COLORS['text']};
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        margin-top: 10px;
        padding: 8px 6px 6px 6px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 8px;
        top: 2px;
        padding: 0 4px;
        color: {COLORS['text_secondary']};
    }}
    
    QPushButton {{
        background-color: {COLORS['primary']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        padding: 5px 10px;
        font-size: 11px;
    }}
    QPushButton:hover {{
        background-color: {COLORS['surface_elevated']};
        border-color: {COLORS['accent']};
    }}
    QPushButton:pressed {{
        background-color: {COLORS['accent']};
    }}
    QPushButton:checked {{
        background-color: {COLORS['accent']};
        color: white;
    }}
    QPushButton:disabled {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_muted']};
    }}
    
    QLabel {{
        color: {COLORS['text']};
        font-size: 11px;
    }}
    
    QListWidget {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        font-size: 10px;
        padding: 2px;
    }}
    QListWidget::item {{
        padding: 4px 6px;
    }}
    QListWidget::item:selected {{
        background-color: {COLORS['accent']};
        color: white;
    }}
    QListWidget::item:hover:!selected {{
        background-color: {COLORS['selection']};
    }}
    
    QSpinBox {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        padding: 4px 6px;
        font-size: 11px;
    }}
    QSpinBox:focus {{
        border-color: {COLORS['accent']};
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: {COLORS['primary']};
        border: none;
        width: 16px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {COLORS['accent']};
    }}
    
    QComboBox {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        padding: 4px 8px;
        font-size: 11px;
    }}
    QComboBox:focus {{
        border-color: {COLORS['accent']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
        background-color: {COLORS['primary']};
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLORS['surface']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        selection-background-color: {COLORS['accent']};
    }}
    
    QProgressBar {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 3px;
        text-align: center;
        color: {COLORS['text']};
        font-size: 10px;
        max-height: 16px;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS['accent']};
        border-radius: 2px;
    }}
    
    QSlider::groove:horizontal {{
        background: {COLORS['surface']};
        height: 4px;
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {COLORS['accent']};
        width: 12px;
        height: 12px;
        margin: -4px 0;
        border-radius: 6px;
    }}
    QSlider::sub-page:horizontal {{
        background: {COLORS['accent']};
        border-radius: 2px;
    }}
    
    QScrollBar:vertical {{
        background-color: {COLORS['surface']};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {COLORS['border']};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['accent']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    QMessageBox {{
        background-color: {COLORS['surface']};
    }}
    QMessageBox QLabel {{
        color: {COLORS['text']};
    }}
    
    QToolTip {{
        background-color: {COLORS['surface_elevated']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
        padding: 4px;
        font-size: 10px;
    }}
"""


# Unified button style - all buttons same base style
BUTTON_STYLES = {
    'primary': f"""
        background-color: {COLORS['accent']};
        color: white;
        border: none;
    """,
    'success': f"""
        background-color: {COLORS['accent']};
        color: white;
        border: none;
    """,
    'danger': f"""
        background-color: {COLORS['danger']};
        color: white;
        border: none;
    """,
    'warning': f"""
        background-color: {COLORS['primary']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
    """,
    'info': f"""
        background-color: {COLORS['primary']};
        color: {COLORS['text']};
        border: 1px solid {COLORS['border']};
    """,
}


PANEL_STYLE = f"""
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
"""

CANVAS_STYLE = f"""
    background-color: {COLORS['canvas']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
"""

INFO_LABEL_STYLE = f"""
    color: {COLORS['text_secondary']};
    font-size: 10px;
    padding: 4px;
"""

STATUS_SUCCESS_STYLE = f"""
    color: {COLORS['accent']};
    font-size: 10px;
"""

STATUS_ERROR_STYLE = f"""
    color: {COLORS['danger']};
    font-size: 10px;
"""

HINT_LABEL_STYLE = f"""
    color: {COLORS['text_muted']};
    font-size: 9px;
"""

TITLE_LABEL_STYLE = f"""
    color: {COLORS['text']};
    font-size: 12px;
    font-weight: 600;
"""
