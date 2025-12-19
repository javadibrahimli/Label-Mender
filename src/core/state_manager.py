"""State management for undo/redo operations."""

import copy
from collections import deque
from typing import List, Dict, Optional
from ..config.constants import MAX_UNDO_STACK_SIZE


class StateManager:
    """Manages undo/redo state for annotations."""
    
    def __init__(self):
        self.undo_stack = deque(maxlen=MAX_UNDO_STACK_SIZE)
        self.redo_stack = deque(maxlen=MAX_UNDO_STACK_SIZE)
    
    def clear(self):
        """Clear both undo and redo stacks."""
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    def save_state(self, boxes: List[Dict]):
        """
        Save current state to undo stack.
        
        Args:
            boxes: Current list of boxes
        """
        self.undo_stack.append(copy.deepcopy(boxes))
        self.redo_stack.clear()
    
    def undo(self, current_boxes: List[Dict]) -> Optional[List[Dict]]:
        """
        Undo last operation.
        
        Args:
            current_boxes: Current list of boxes
            
        Returns:
            Previous state or None if no undo available
        """
        if not self.undo_stack:
            return None
        
        self.redo_stack.append(copy.deepcopy(current_boxes))
        return self.undo_stack.pop()
    
    def redo(self, current_boxes: List[Dict]) -> Optional[List[Dict]]:
        """
        Redo last undone operation.
        
        Args:
            current_boxes: Current list of boxes
            
        Returns:
            Next state or None if no redo available
        """
        if not self.redo_stack:
            return None
        
        self.undo_stack.append(copy.deepcopy(current_boxes))
        return self.redo_stack.pop()
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0
