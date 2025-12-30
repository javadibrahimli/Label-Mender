"""Model management for YOLO inference."""

import os
import cv2
import numpy as np
from typing import Dict, List, Optional


class ModelManager:
    
    def __init__(self):
        self.model = None
        self.model_path = ""
        self.model_type = None
        
        self.yolov4_net = None
        self.yolov4_cfg_path = ""
        self.yolov4_weights_path = ""
        self.yolov4_names_path = ""
        self.yolov4_class_names = {}
        self.yolov4_input_width = 416
        self.yolov4_input_height = 416
        
    def load_model(self, path: str) -> bool:
        try:
            from ultralytics import YOLO
            self.model = YOLO(path)
            self.model_path = path
            self.model_type = 'ultralytics'
            self.yolov4_net = None
            self.yolov4_class_names = {}
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def load_yolov4_model(self, cfg_path: str, weights_path: str, names_path: str) -> bool:
        try:
            self.yolov4_net = cv2.dnn.readNetFromDarknet(cfg_path, weights_path)
            self.yolov4_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.yolov4_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            
            try:
                if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                    self.yolov4_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                    self.yolov4_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            except:
                pass
            
            self.yolov4_class_names = self._load_names_file(names_path)
            self._parse_cfg_input_size(cfg_path)
            
            self.yolov4_cfg_path = cfg_path
            self.yolov4_weights_path = weights_path
            self.yolov4_names_path = names_path
            self.model_path = weights_path
            self.model_type = 'yolov4'
            self.model = None
            
            return True
        except Exception as e:
            print(f"Error loading YOLOv4 model: {e}")
            return False
    
    def _load_names_file(self, names_path: str) -> Dict[int, str]:
        class_names = {}
        try:
            with open(names_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    name = line.strip()
                    if name:
                        class_names[i] = name
        except Exception as e:
            print(f"Error loading names file: {e}")
        return class_names
    
    def _parse_cfg_input_size(self, cfg_path: str) -> None:
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('width='):
                        self.yolov4_input_width = int(line.split('=')[1])
                    elif line.startswith('height='):
                        self.yolov4_input_height = int(line.split('=')[1])
        except Exception as e:
            print(f"Error parsing cfg file: {e}")
            self.yolov4_input_width = 416
            self.yolov4_input_height = 416
    
    def is_loaded(self) -> bool:
        return self.model is not None or self.yolov4_net is not None
    
    def get_model_name(self) -> str:
        if self.model_path:
            return os.path.basename(self.model_path)
        return "Not loaded"
    
    def get_model_type(self) -> Optional[str]:
        return self.model_type
    
    def get_class_names(self) -> Dict[int, str]:
        if self.model_type == 'yolov4':
            return self.yolov4_class_names
        elif self.model and hasattr(self.model, 'names'):
            return self.model.names
        return {}
    
    def run_inference(self, image_path: str, confidence: float = 0.25) -> List[Dict]:
        if self.model_type == 'yolov4':
            return self._run_yolov4_inference(image_path, confidence)
        elif self.model_type == 'ultralytics':
            return self._run_ultralytics_inference(image_path, confidence)
        return []
    
    def _run_ultralytics_inference(self, image_path: str, confidence: float) -> List[Dict]:
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
    
    def _run_yolov4_inference(self, image_path: str, confidence: float) -> List[Dict]:
        if not self.yolov4_net:
            return []
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            img_height, img_width = image.shape[:2]
            
            blob = cv2.dnn.blobFromImage(
                image, 
                1/255.0, 
                (self.yolov4_input_width, self.yolov4_input_height),
                swapRB=True, 
                crop=False
            )
            
            self.yolov4_net.setInput(blob)
            
            layer_names = self.yolov4_net.getLayerNames()
            try:
                output_layers = [layer_names[i - 1] for i in self.yolov4_net.getUnconnectedOutLayers().flatten()]
            except:
                output_layers = [layer_names[i[0] - 1] for i in self.yolov4_net.getUnconnectedOutLayers()]
            
            outputs = self.yolov4_net.forward(output_layers)
            
            detections = []
            boxes = []
            confidences = []
            class_ids = []
            
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    conf = float(scores[class_id])
                    
                    if conf >= confidence:
                        center_x = detection[0]
                        center_y = detection[1]
                        w = detection[2]
                        h = detection[3]
                        
                        x_px = int((center_x - w/2) * img_width)
                        y_px = int((center_y - h/2) * img_height)
                        w_px = int(w * img_width)
                        h_px = int(h * img_height)
                        
                        boxes.append([x_px, y_px, w_px, h_px])
                        confidences.append(conf)
                        class_ids.append(int(class_id))
            
            if len(boxes) > 0:
                indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence, 0.4)
                
                if len(indices) > 0:
                    if isinstance(indices, np.ndarray):
                        indices = indices.flatten()
                    else:
                        indices = [i[0] if isinstance(i, (list, tuple, np.ndarray)) else i for i in indices]
                    
                    for i in indices:
                        x_px, y_px, w_px, h_px = boxes[i]
                        
                        cx = (x_px + w_px/2) / img_width
                        cy = (y_px + h_px/2) / img_height
                        nw = w_px / img_width
                        nh = h_px / img_height
                        
                        detections.append({
                            'class': class_ids[i],
                            'x': cx,
                            'y': cy,
                            'w': nw,
                            'h': nh,
                            'conf': confidences[i]
                        })
            
            return detections
            
        except Exception as e:
            print(f"Error during YOLOv4 inference: {e}")
            return []
