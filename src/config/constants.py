"""Application constants and enums."""

from enum import IntEnum


# Professional dark theme color scheme
COLORS = {
    # Primary palette
    'primary': '#3c3c3c',
    'secondary': '#3c3c3c',
    'accent': '#007acc',
    'accent_hover': '#1c97ea',
    
    # Semantic colors
    'success': '#007acc',
    'warning': '#007acc',
    'danger': '#c42b1c',
    'info': '#007acc',
    
    # Text colors
    'text': '#cccccc',
    'text_secondary': '#969696',
    'text_muted': '#6e6e6e',
    'text_dark': '#252526',
    
    # Background colors
    'background': '#252526',
    'surface': '#2d2d2d',
    'surface_elevated': '#3c3c3c',
    'panel': '#2d2d2d',
    'canvas': '#1e1e1e',
    
    # Border colors
    'border': '#3c3c3c',
    'border_light': '#3c3c3c',
    'border_focus': '#007acc',
    
    # Special
    'selection': 'rgba(0, 122, 204, 0.3)',
}


# Handle positions for resize operations
class HandlePosition(IntEnum):
    """Enumeration for box handle positions."""
    NONE = 0
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_LEFT = 3
    BOTTOM_RIGHT = 4
    TOP = 5
    BOTTOM = 6
    LEFT = 7
    RIGHT = 8
    MOVE = 9


# Size of resize handles in pixels
HANDLE_SIZE = 10


# Default model path
DEFAULT_MODEL_PATH = "runs/detect/iran_syria_v1/weights/best.pt"


# Valid image extensions
VALID_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp']

# Valid video extensions
VALID_VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']


# Minimum box size (as fraction of image)
MIN_BOX_SIZE = 0.01


# Default confidence threshold
DEFAULT_CONFIDENCE = 0.25


# Undo/Redo stack size
MAX_UNDO_STACK_SIZE = 50
