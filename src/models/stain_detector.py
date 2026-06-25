from ultralytics import YOLO
import numpy as np
import cv2
import os

class StainDetector:
    def __init__(self, model_path=r"runs\detect\stain_detector_v1\weights\best.pt"):
        """
        Initializes the custom trained YOLOv8 Stain Detector.
        If the custom model is not found, it will gracefully fail or prompt training.
        """
        self.model_path = model_path
        
        # Resolve path robustly relative to script location if needed
        resolved_path = model_path
        if not os.path.exists(resolved_path):
            resolved_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), model_path)
            
        try:
            self.model = YOLO(resolved_path)
            self.is_loaded = True
            print(f"[StainDetector] Loaded YOLO model from {resolved_path}")
        except Exception as e:
            print(f"Failed to load YOLO model from {resolved_path}: {e}")
            self.is_loaded = False

    def detect_stains(self, image_np: np.ndarray):
        """
        Detects stains in an image.
        Returns: A list of dictionaries containing stain bounding boxes and confidence.
                 And an annotated image (numpy array).
        """
        if not self.is_loaded:
            return [], image_np

        # Run inference
        # In production, we would use UV/Multispectral images as well
        results = self.model(image_np, verbose=False)
        
        stains = []
        annotated_img = image_np.copy()
        
        for result in results:
            annotated_img = result.plot()  # YOLO's built-in plotting
            boxes = result.boxes
            for box in boxes:
                # We would filter by our specific stain classes
                # (e.g., class_id 0=oil, 1=blood, 2=rust)
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                
                stains.append({
                    "class_id": cls_id,
                    "confidence": conf,
                    "bbox": xyxy
                })
                
        return stains, annotated_img

