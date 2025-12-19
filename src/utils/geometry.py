"""Geometry utilities for bounding box operations."""

from PyQt5.QtCore import QRect
from ..config.constants import MIN_BOX_SIZE


class BoxGeometry:
    """Handles geometric calculations for bounding boxes."""
    
    @staticmethod
    def get_box_rect_px(box, original_width, original_height, scale_factor_x, scale_factor_y):
        """
        Get box rectangle in pixel coordinates.
        
        Args:
            box: Dictionary with 'x', 'y', 'w', 'h' in normalized coordinates
            original_width: Original image width
            original_height: Original image height
            scale_factor_x: X-axis scale factor
            scale_factor_y: Y-axis scale factor
            
        Returns:
            QRect object in pixel coordinates or None
        """
        if not original_width or not original_height:
            return None
        
        w_px = box['w'] * original_width * scale_factor_x
        h_px = box['h'] * original_height * scale_factor_y
        x_px = (box['x'] * original_width * scale_factor_x) - (w_px / 2)
        y_px = (box['y'] * original_height * scale_factor_y) - (h_px / 2)
        
        return QRect(int(x_px), int(y_px), int(w_px), int(h_px))
    
    @staticmethod
    def normalize_box_coords(x1, y1, x2, y2, image_width, image_height):
        """
        Convert pixel coordinates to normalized YOLO format.
        
        Args:
            x1, y1, x2, y2: Corner coordinates in pixels
            image_width, image_height: Image dimensions
            
        Returns:
            Dictionary with normalized 'x', 'y', 'w', 'h'
        """
        box_w = max(MIN_BOX_SIZE, min(1, (x2 - x1) / image_width))
        box_h = max(MIN_BOX_SIZE, min(1, (y2 - y1) / image_height))
        center_x = max(0, min(1, (x1 + (x2 - x1) / 2) / image_width))
        center_y = max(0, min(1, (y1 + (y2 - y1) / 2) / image_height))
        
        return {
            'x': center_x,
            'y': center_y,
            'w': box_w,
            'h': box_h
        }
    
    @staticmethod
    def clamp_box_to_bounds(left, right, top, bottom):
        """
        Clamp box edges to image bounds [0, 1].
        
        Args:
            left, right, top, bottom: Box edges in normalized coordinates
            
        Returns:
            Tuple of (left, right, top, bottom) clamped to [0, 1]
        """
        return (
            max(0, min(1, left)),
            max(0, min(1, right)),
            max(0, min(1, top)),
            max(0, min(1, bottom))
        )
    
    @staticmethod
    def edges_to_center_format(left, right, top, bottom):
        """
        Convert edge coordinates to center format.
        
        Args:
            left, right, top, bottom: Edge coordinates
            
        Returns:
            Dictionary with 'x', 'y', 'w', 'h' in center format
        """
        return {
            'x': (left + right) / 2,
            'y': (top + bottom) / 2,
            'w': right - left,
            'h': bottom - top
        }
