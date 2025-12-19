"""Model management for YOLO inference."""

import os
from typing import Dict, List, Optional


class ModelManager:
    """Manages YOLO model loading and inference."""
    
    def __init__(self):
        self.model = None
        self.model_path = ""
        
    def load_model(self, path: str) -> bool:
        """
        Load YOLO model from file.
        
        Args:
            path: Path to model file
            
        Returns:
            True if successful
        """
        try:
            from ultralytics import YOLO
            self.model = YOLO(path)
            self.model_path = path
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None
    
    def get_model_name(self) -> str:
        """Get the basename of the loaded model."""
        if self.model_path:
            return os.path.basename(self.model_path)
        return "Not loaded"
    
    def get_class_names(self) -> Dict[int, str]:
        """
        Get class names from model.
        
        Returns:
            Dictionary mapping class ID to name
        """
        if self.model and hasattr(self.model, 'names'):
            return self.model.names
        return {}
    
    def run_inference(self, image_path: str, confidence: float = 0.25) -> List[Dict]:
        """
        Run inference on image.
        
        Args:
            image_path: Path to image
            confidence: Confidence threshold
            
        Returns:
            List of detected boxes
        """
        if not self.model:
            return []
        
        results = self.model(image_path)
        detections = []
        
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                x, y, w, h = box.xywhn[0].tolist()
                conf = float(box.conf[0])
                
                if conf >= confidence:
                    detections.append({
                        'class': cls,
                        'x': x,
                        'y': y,
                        'w': w,
                        'h': h,
                        'conf': conf
                    })
        
        return detections
