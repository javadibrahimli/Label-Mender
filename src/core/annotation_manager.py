"""Annotation management for bounding boxes."""

import copy
from typing import List, Dict, Optional


class AnnotationManager:
    """Manages annotation boxes and operations."""
    
    def __init__(self):
        self.boxes: List[Dict] = []
        self.selected_index: int = -1
        
    def clear(self):
        """Clear all boxes."""
        self.boxes = []
        self.selected_index = -1
    
    def set_boxes(self, boxes: List[Dict]):
        """Set the current boxes."""
        self.boxes = boxes
        self.selected_index = -1
    
    def get_boxes(self) -> List[Dict]:
        """Get all boxes."""
        return self.boxes
    
    def add_box(self, box: Dict) -> int:
        """
        Add a new box.
        
        Args:
            box: Box dictionary
            
        Returns:
            Index of added box
        """
        self.boxes.append(box)
        return len(self.boxes) - 1
    
    def delete_box(self, index: int) -> bool:
        """
        Delete box at index.
        
        Args:
            index: Box index
            
        Returns:
            True if successful
        """
        if 0 <= index < len(self.boxes):
            del self.boxes[index]
            self.selected_index = -1
            return True
        return False
    
    def update_box_class(self, index: int, class_id: int) -> bool:
        """
        Update class of box.
        
        Args:
            index: Box index
            class_id: New class ID
            
        Returns:
            True if successful
        """
        if 0 <= index < len(self.boxes):
            self.boxes[index]['class'] = class_id
            return True
        return False
    
    def get_selected_box(self) -> Optional[Dict]:
        """Get the currently selected box."""
        if 0 <= self.selected_index < len(self.boxes):
            return self.boxes[self.selected_index]
        return None
    
    def select_box(self, index: int):
        """Select box at index."""
        if 0 <= index < len(self.boxes):
            self.selected_index = index
        else:
            self.selected_index = -1
    
    def deselect(self):
        """Deselect current box."""
        self.selected_index = -1
    
    def sort_boxes_by_x(self):
        """Sort boxes by x coordinate (left to right)."""
        self.boxes = sorted(self.boxes, key=lambda b: b['x'])
        self.selected_index = -1
    
    def get_sorted_indices(self) -> List[int]:
        """
        Get indices sorted by x coordinate.
        
        Returns:
            List of indices sorted left to right
        """
        return sorted(range(len(self.boxes)), key=lambda i: self.boxes[i]['x'])
    
    def get_plate_reading(self, class_names: Dict[int, str]) -> str:
        """
        Get plate reading from sorted boxes.
        
        Args:
            class_names: Dictionary mapping class ID to name
            
        Returns:
            String with concatenated class names
        """
        if not self.boxes:
            return ""
        
        sorted_boxes = sorted(self.boxes, key=lambda b: b['x'])
        return " ".join(
            class_names.get(b['class'], f"Class {b['class']}") 
            for b in sorted_boxes
        )
    
    def filter_by_confidence(self, raw_detections: List[Dict], threshold: float) -> List[Dict]:
        """
        Filter detections by confidence threshold.
        
        Args:
            raw_detections: List of all detections
            threshold: Confidence threshold
            
        Returns:
            Filtered list of detections
        """
        return [
            b.copy() for b in raw_detections 
            if b.get('conf', 1.0) >= threshold
        ]
