"""Interactive image canvas widget with zoom and pan."""

import copy
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QPoint
from ..config.constants import HANDLE_SIZE, HandlePosition, MIN_BOX_SIZE
from ..utils.geometry import BoxGeometry


class ImageCanvas(QLabel):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setMouseTracking(True)
        
        self.drawing = False
        self.start_point = None
        self.end_point = None
        
        self.dragging = False
        self.drag_handle = HandlePosition.NONE
        self.drag_start = None
        self.drag_box_original = None
        
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 5.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.panning = False
        self.pan_start = None
        self.pan_start_offset = None
    
    def reset_view(self):
        self.zoom_level = 1.0
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        if self.parent_window:
            self.parent_window.draw_boxes()
    
    def get_handle_at(self, pos, box_idx):
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
            self.parent_window.scale_factor_x * self.zoom_level,
            self.parent_window.scale_factor_y * self.zoom_level
        )
        
        if not rect:
            return HandlePosition.NONE
        
        from PyQt5.QtCore import Qt
        base_scaled = self.parent_window.original_pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        zoomed_w = int(base_scaled.width() * self.zoom_level)
        zoomed_h = int(base_scaled.height() * self.zoom_level)
        zoomed_offset_x = (self.width() - zoomed_w) / 2
        zoomed_offset_y = (self.height() - zoomed_h) / 2
        
        adj_offset_x = zoomed_offset_x + self.pan_offset_x
        adj_offset_y = zoomed_offset_y + self.pan_offset_y
        
        x = pos.x() - adj_offset_x
        y = pos.y() - adj_offset_y
        
        hs = HANDLE_SIZE
        
        if abs(x - rect.left()) <= hs and abs(y - rect.top()) <= hs:
            return HandlePosition.TOP_LEFT
        if abs(x - rect.right()) <= hs and abs(y - rect.top()) <= hs:
            return HandlePosition.TOP_RIGHT
        if abs(x - rect.left()) <= hs and abs(y - rect.bottom()) <= hs:
            return HandlePosition.BOTTOM_LEFT
        if abs(x - rect.right()) <= hs and abs(y - rect.bottom()) <= hs:
            return HandlePosition.BOTTOM_RIGHT
        
        if rect.left() <= x <= rect.right() and abs(y - rect.top()) <= hs:
            return HandlePosition.TOP
        if rect.left() <= x <= rect.right() and abs(y - rect.bottom()) <= hs:
            return HandlePosition.BOTTOM
        if rect.top() <= y <= rect.bottom() and abs(x - rect.left()) <= hs:
            return HandlePosition.LEFT
        if rect.top() <= y <= rect.bottom() and abs(x - rect.right()) <= hs:
            return HandlePosition.RIGHT
        
        if rect.contains(int(x), int(y)):
            return HandlePosition.MOVE
        
        return HandlePosition.NONE
    
    def get_cursor_for_handle(self, handle):
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
    
    def wheelEvent(self, event):
        if not self.parent_window or not self.parent_window.original_pixmap:
            return
        
        old_zoom = self.zoom_level
        
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_level = min(self.zoom_level * 1.15, self.max_zoom)
        else:
            self.zoom_level = max(self.zoom_level / 1.15, self.min_zoom)
        
        if old_zoom != self.zoom_level:
            self.parent_window.draw_boxes()
            self.parent_window.update_zoom_label()
    
    def mousePressEvent(self, event):
        if not self.parent_window:
            return
        
        if event.button() == Qt.MiddleButton:
            self.panning = True
            self.pan_start = event.pos()
            self.pan_start_offset = (self.pan_offset_x, self.pan_offset_y)
            self.setCursor(Qt.ClosedHandCursor)
            return
        
        if event.button() == Qt.LeftButton:
            if self.parent_window.mask_mode:
                self.drawing = True
                self.start_point = event.pos()
                self.end_point = event.pos()
            elif self.parent_window.draw_mode:
                self.drawing = True
                self.start_point = event.pos()
                self.end_point = event.pos()
            else:
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
                
                self.parent_window.select_box_at(event.pos().x(), event.pos().y())
                
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
        if not self.parent_window:
            return
        
        if self.panning:
            dx = event.pos().x() - self.pan_start.x()
            dy = event.pos().y() - self.pan_start.y()
            self.pan_offset_x = self.pan_start_offset[0] + dx
            self.pan_offset_y = self.pan_start_offset[1] + dy
            self.parent_window.draw_boxes()
            return
        
        if self.parent_window.mask_mode:
            if self.drawing:
                self.end_point = event.pos()
                self.parent_window.draw_temp_mask(self.start_point, self.end_point)
            else:
                self.setCursor(Qt.CrossCursor)
        elif self.parent_window.draw_mode:
            if self.drawing:
                self.end_point = event.pos()
                self.parent_window.draw_temp_box(self.start_point, self.end_point)
            else:
                self.setCursor(Qt.CrossCursor)
        elif self.dragging and self.drag_handle != HandlePosition.NONE:
            self.update_box_from_drag(event.pos())
        else:
            selected_idx = self.parent_window.annotation_mgr.selected_index
            if selected_idx >= 0:
                handle = self.get_handle_at(event.pos(), selected_idx)
                self.setCursor(self.get_cursor_for_handle(handle))
            else:
                self.setCursor(Qt.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        if not self.parent_window:
            return
        
        if event.button() == Qt.MiddleButton:
            self.panning = False
            self.pan_start = None
            self.pan_start_offset = None
            self.setCursor(Qt.ArrowCursor)
            return
        
        if event.button() == Qt.LeftButton:
            if self.drawing:
                self.drawing = False
                if self.parent_window.mask_mode and self.start_point and self.end_point:
                    self.parent_window.finalize_new_mask(self.start_point, self.end_point)
                elif self.parent_window.draw_mode and self.start_point and self.end_point:
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
        if not self.parent_window or not self.drag_box_original:
            return
        
        selected_idx = self.parent_window.annotation_mgr.selected_index
        if selected_idx < 0:
            return
        
        if not self.parent_window.original_pixmap:
            return
        
        orig_w = self.parent_window.original_pixmap.width()
        orig_h = self.parent_window.original_pixmap.height()
        
        dx = (current_pos.x() - self.drag_start.x()) / (self.parent_window.scale_factor_x * self.zoom_level) / orig_w
        dy = (current_pos.y() - self.drag_start.y()) / (self.parent_window.scale_factor_y * self.zoom_level) / orig_h
        
        boxes = self.parent_window.annotation_mgr.get_boxes()
        box = boxes[selected_idx]
        orig = self.drag_box_original
        
        orig_left = orig['x'] - orig['w'] / 2
        orig_right = orig['x'] + orig['w'] / 2
        orig_top = orig['y'] - orig['h'] / 2
        orig_bottom = orig['y'] + orig['h'] / 2
        
        new_left, new_right = orig_left, orig_right
        new_top, new_bottom = orig_top, orig_bottom
        
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
        
        new_left, new_right, new_top, new_bottom = BoxGeometry.clamp_box_to_bounds(
            new_left, new_right, new_top, new_bottom
        )
        
        result = BoxGeometry.edges_to_center_format(new_left, new_right, new_top, new_bottom)
        box.update(result)
        
        self.parent_window.draw_boxes()
