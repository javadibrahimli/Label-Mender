"""Interactive image canvas widget for drawing and editing boxes."""

import copy
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPixmap
from PyQt5.QtCore import Qt, QRect, QPoint
from ..config.constants import HANDLE_SIZE, HandlePosition, MIN_BOX_SIZE
from ..utils.geometry import BoxGeometry


class ImageCanvas(QLabel):
    """Custom widget for image display with box drawing, moving, and resizing."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setMouseTracking(True)
        
        # Drawing new box
        self.drawing = False
        self.start_point = None
        self.end_point = None
        
        # Moving/resizing existing box
        self.dragging = False
        self.drag_handle = HandlePosition.NONE
        self.drag_start = None
        self.drag_box_original = None
    
    def get_handle_at(self, pos, box_idx):
        """
        Check if position is on a resize handle or inside the box.
        
        Args:
            pos: Mouse position
            box_idx: Index of box to check
            
        Returns:
            HandlePosition enum value
        """
        if not self.parent_window or box_idx < 0:
            return HandlePosition.NONE
        
        boxes = self.parent_window.annotation_mgr.get_boxes()
        if box_idx >= len(boxes):
            return HandlePosition.NONE
        
        box = boxes[box_idx]
        rect = BoxGeometry.get_box_rect_px(
            box,
            self.parent_window.original_pixmap.width() if self.parent_window.original_pixmap else 0,
            self.parent_window.original_pixmap.height() if self.parent_window.original_pixmap else 0,
            self.parent_window.scale_factor_x,
            self.parent_window.scale_factor_y
        )
        
        if not rect:
            return HandlePosition.NONE
        
        # Convert to image coordinates
        x = pos.x() - self.parent_window.offset_x
        y = pos.y() - self.parent_window.offset_y
        
        hs = HANDLE_SIZE
        
        # Check corners first (they take priority)
        if abs(x - rect.left()) <= hs and abs(y - rect.top()) <= hs:
            return HandlePosition.TOP_LEFT
        if abs(x - rect.right()) <= hs and abs(y - rect.top()) <= hs:
            return HandlePosition.TOP_RIGHT
        if abs(x - rect.left()) <= hs and abs(y - rect.bottom()) <= hs:
            return HandlePosition.BOTTOM_LEFT
        if abs(x - rect.right()) <= hs and abs(y - rect.bottom()) <= hs:
            return HandlePosition.BOTTOM_RIGHT
        
        # Check edges
        if rect.left() <= x <= rect.right() and abs(y - rect.top()) <= hs:
            return HandlePosition.TOP
        if rect.left() <= x <= rect.right() and abs(y - rect.bottom()) <= hs:
            return HandlePosition.BOTTOM
        if rect.top() <= y <= rect.bottom() and abs(x - rect.left()) <= hs:
            return HandlePosition.LEFT
        if rect.top() <= y <= rect.bottom() and abs(x - rect.right()) <= hs:
            return HandlePosition.RIGHT
        
        # Check if inside box (for moving)
        if rect.contains(int(x), int(y)):
            return HandlePosition.MOVE
        
        return HandlePosition.NONE
    
    def get_cursor_for_handle(self, handle):
        """Get appropriate cursor for handle type."""
        cursor_map = {
            HandlePosition.TOP_LEFT: Qt.SizeFDiagCursor,
            HandlePosition.BOTTOM_RIGHT: Qt.SizeFDiagCursor,
            HandlePosition.TOP_RIGHT: Qt.SizeBDiagCursor,
            HandlePosition.BOTTOM_LEFT: Qt.SizeBDiagCursor,
            HandlePosition.TOP: Qt.SizeVerCursor,
            HandlePosition.BOTTOM: Qt.SizeVerCursor,
            HandlePosition.LEFT: Qt.SizeHorCursor,
            HandlePosition.RIGHT: Qt.SizeHorCursor,
            HandlePosition.MOVE: Qt.SizeAllCursor,
        }
        return cursor_map.get(handle, Qt.ArrowCursor)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if not self.parent_window:
            return
        
        if event.button() == Qt.LeftButton:
            if self.parent_window.draw_mode:
                # Drawing new box
                self.drawing = True
                self.start_point = event.pos()
                self.end_point = event.pos()
            else:
                # Check if clicking on selected box handle
                selected_idx = self.parent_window.annotation_mgr.selected_index
                if selected_idx >= 0:
                    handle = self.get_handle_at(event.pos(), selected_idx)
                    if handle != HandlePosition.NONE:
                        self.dragging = True
                        self.drag_handle = handle
                        self.drag_start = event.pos()
                        boxes = self.parent_window.annotation_mgr.get_boxes()
                        self.drag_box_original = copy.deepcopy(boxes[selected_idx])
                        self.parent_window.state_mgr.save_state(boxes)
                        return
                
                # Try to select a box
                self.parent_window.select_box_at(event.pos().x(), event.pos().y())
                
                # After selection, check if we can start dragging
                selected_idx = self.parent_window.annotation_mgr.selected_index
                if selected_idx >= 0:
                    handle = self.get_handle_at(event.pos(), selected_idx)
                    if handle != HandlePosition.NONE:
                        self.dragging = True
                        self.drag_handle = handle
                        self.drag_start = event.pos()
                        boxes = self.parent_window.annotation_mgr.get_boxes()
                        self.drag_box_original = copy.deepcopy(boxes[selected_idx])
                        self.parent_window.state_mgr.save_state(boxes)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if not self.parent_window:
            return
        
        if self.parent_window.draw_mode:
            if self.drawing:
                self.end_point = event.pos()
                self.parent_window.draw_temp_box(self.start_point, self.end_point)
            else:
                self.setCursor(Qt.CrossCursor)
        elif self.dragging and self.drag_handle != HandlePosition.NONE:
            self.update_box_from_drag(event.pos())
        else:
            # Update cursor based on hover
            selected_idx = self.parent_window.annotation_mgr.selected_index
            if selected_idx >= 0:
                handle = self.get_handle_at(event.pos(), selected_idx)
                self.setCursor(self.get_cursor_for_handle(handle))
            else:
                self.setCursor(Qt.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if not self.parent_window:
            return
        
        if event.button() == Qt.LeftButton:
            if self.drawing:
                self.drawing = False
                if self.parent_window.draw_mode and self.start_point and self.end_point:
                    self.parent_window.finalize_new_box(self.start_point, self.end_point)
                self.start_point = None
                self.end_point = None
            elif self.dragging:
                self.dragging = False
                self.drag_handle = HandlePosition.NONE
                self.drag_start = None
                self.drag_box_original = None
                self.parent_window.update_list_widget()
    
    def update_box_from_drag(self, current_pos):
        """Update the selected box based on drag operation."""
        if not self.parent_window or not self.drag_box_original:
            return
        
        selected_idx = self.parent_window.annotation_mgr.selected_index
        if selected_idx < 0:
            return
        
        if not self.parent_window.original_pixmap:
            return
        
        orig_w = self.parent_window.original_pixmap.width()
        orig_h = self.parent_window.original_pixmap.height()
        
        # Calculate delta in image coordinates
        dx = (current_pos.x() - self.drag_start.x()) / self.parent_window.scale_factor_x / orig_w
        dy = (current_pos.y() - self.drag_start.y()) / self.parent_window.scale_factor_y / orig_h
        
        boxes = self.parent_window.annotation_mgr.get_boxes()
        box = boxes[selected_idx]
        orig = self.drag_box_original
        
        # Get original box edges in normalized coordinates
        orig_left = orig['x'] - orig['w'] / 2
        orig_right = orig['x'] + orig['w'] / 2
        orig_top = orig['y'] - orig['h'] / 2
        orig_bottom = orig['y'] + orig['h'] / 2
        
        new_left, new_right = orig_left, orig_right
        new_top, new_bottom = orig_top, orig_bottom
        
        # Apply drag based on handle type
        if self.drag_handle == HandlePosition.MOVE:
            new_left = orig_left + dx
            new_right = orig_right + dx
            new_top = orig_top + dy
            new_bottom = orig_bottom + dy
        elif self.drag_handle == HandlePosition.TOP_LEFT:
            new_left = min(orig_left + dx, orig_right - MIN_BOX_SIZE)
            new_top = min(orig_top + dy, orig_bottom - MIN_BOX_SIZE)
        elif self.drag_handle == HandlePosition.TOP_RIGHT:
            new_right = max(orig_right + dx, orig_left + MIN_BOX_SIZE)
            new_top = min(orig_top + dy, orig_bottom - MIN_BOX_SIZE)
        elif self.drag_handle == HandlePosition.BOTTOM_LEFT:
            new_left = min(orig_left + dx, orig_right - MIN_BOX_SIZE)
            new_bottom = max(orig_bottom + dy, orig_top + MIN_BOX_SIZE)
        elif self.drag_handle == HandlePosition.BOTTOM_RIGHT:
            new_right = max(orig_right + dx, orig_left + MIN_BOX_SIZE)
            new_bottom = max(orig_bottom + dy, orig_top + MIN_BOX_SIZE)
        elif self.drag_handle == HandlePosition.TOP:
            new_top = min(orig_top + dy, orig_bottom - MIN_BOX_SIZE)
        elif self.drag_handle == HandlePosition.BOTTOM:
            new_bottom = max(orig_bottom + dy, orig_top + MIN_BOX_SIZE)
        elif self.drag_handle == HandlePosition.LEFT:
            new_left = min(orig_left + dx, orig_right - MIN_BOX_SIZE)
        elif self.drag_handle == HandlePosition.RIGHT:
            new_right = max(orig_right + dx, orig_left + MIN_BOX_SIZE)
        
        # Clamp to image bounds
        new_left, new_right, new_top, new_bottom = BoxGeometry.clamp_box_to_bounds(
            new_left, new_right, new_top, new_bottom
        )
        
        # Update box
        result = BoxGeometry.edges_to_center_format(new_left, new_right, new_top, new_bottom)
        box.update(result)
        
        self.parent_window.draw_boxes()
