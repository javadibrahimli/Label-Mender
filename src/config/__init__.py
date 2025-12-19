"""Configuration package for Label Mender application."""

# Centralized version - update this for new releases
__version__ = "1.0.0"
VERSION = f"v{__version__}"

from .constants import (
    COLORS, 
    HANDLE_SIZE, 
    HandlePosition,
    DEFAULT_MODEL_PATH,
    VALID_IMAGE_EXTENSIONS,
    DEFAULT_CONFIDENCE,
    MIN_BOX_SIZE,
    MAX_UNDO_STACK_SIZE
)
from .styles import (
    STYLESHEET,
    BUTTON_STYLES,
    PANEL_STYLE,
    CANVAS_STYLE,
    INFO_LABEL_STYLE,
    STATUS_SUCCESS_STYLE,
    STATUS_ERROR_STYLE,
    HINT_LABEL_STYLE,
    TITLE_LABEL_STYLE
)

__all__ = [
    '__version__',
    'VERSION',
    'COLORS', 
    'HANDLE_SIZE', 
    'HandlePosition', 
    'STYLESHEET',
    'DEFAULT_MODEL_PATH',
    'VALID_IMAGE_EXTENSIONS',
    'DEFAULT_CONFIDENCE',
    'MIN_BOX_SIZE',
    'MAX_UNDO_STACK_SIZE',
    'BUTTON_STYLES',
    'PANEL_STYLE',
    'CANVAS_STYLE',
    'INFO_LABEL_STYLE',
    'STATUS_SUCCESS_STYLE',
    'STATUS_ERROR_STYLE',
    'HINT_LABEL_STYLE',
    'TITLE_LABEL_STYLE'
]
