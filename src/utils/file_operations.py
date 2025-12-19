"""File operations utilities."""

import os
import yaml
from typing import List, Dict, Optional


class FileManager:
    """Handles file I/O operations for annotations and classes."""
    
    @staticmethod
    def load_annotations(txt_path: str) -> List[Dict]:
        """
        Load annotations from YOLO format text file.
        
        Args:
            txt_path: Path to annotation file
            
        Returns:
            List of box dictionaries
        """
        boxes = []
        if not os.path.exists(txt_path):
            return boxes
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls = int(parts[0])
                    x, y, w, h = map(float, parts[1:5])
                    conf = float(parts[5]) if len(parts) > 5 else 1.0
                    boxes.append({
                        'class': cls,
                        'x': x,
                        'y': y,
                        'w': w,
                        'h': h,
                        'conf': conf
                    })
        return boxes
    
    @staticmethod
    def save_annotations(txt_path: str, boxes: List[Dict]) -> None:
        """
        Save annotations to YOLO format text file.
        
        Args:
            txt_path: Path to save annotation file
            boxes: List of box dictionaries
        """
        with open(txt_path, 'w', encoding='utf-8') as f:
            for box in boxes:
                f.write(
                    f"{box['class']} {box['x']:.6f} {box['y']:.6f} "
                    f"{box['w']:.6f} {box['h']:.6f}\n"
                )
    
    @staticmethod
    def load_class_names(file_path: str) -> Dict[int, str]:
        """
        Load class names from YAML or text file.
        
        Args:
            file_path: Path to class file
            
        Returns:
            Dictionary mapping class ID to name
        """
        class_names = {}
        
        if file_path.endswith(('.yaml', '.yml')):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if 'names' in data:
                    names = data['names']
                    if isinstance(names, list):
                        class_names = {i: name for i, name in enumerate(names)}
                    elif isinstance(names, dict):
                        class_names = {int(k): v for k, v in names.items()}
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    name = line.strip()
                    if name:
                        class_names[i] = name
        
        return class_names
    
    @staticmethod
    def save_class_names(file_path: str, class_names: Dict[int, str]) -> None:
        """
        Save class names to file.
        
        Args:
            file_path: Path to save class file
            class_names: Dictionary mapping class ID to name
        """
        if file_path.endswith(('.yaml', '.yml')):
            # Load existing YAML or create new one
            data = {}
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
            
            names_list = [
                class_names.get(i, f"class_{i}") 
                for i in range(max(class_names.keys()) + 1)
            ]
            data['names'] = names_list
            data['nc'] = len(names_list)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                for i in range(max(class_names.keys()) + 1):
                    f.write(f"{class_names.get(i, f'class_{i}')}\n")
    
    @staticmethod
    def get_image_list(folder_path: str, extensions: List[str]) -> List[str]:
        """
        Get sorted list of image files in folder.
        
        Args:
            folder_path: Path to image folder
            extensions: List of valid extensions
            
        Returns:
            Sorted list of image filenames
        """
        if not os.path.exists(folder_path):
            return []
        
        return sorted([
            f for f in os.listdir(folder_path) 
            if os.path.splitext(f)[1].lower() in extensions
        ])
    
    @staticmethod
    def annotation_exists(image_folder: str, image_name: str) -> bool:
        """
        Check if annotation file exists for image.
        
        Args:
            image_folder: Path to image folder
            image_name: Image filename
            
        Returns:
            True if annotation exists
        """
        txt_path = os.path.join(
            image_folder, 
            os.path.splitext(image_name)[0] + ".txt"
        )
        return os.path.exists(txt_path)
