import cv2
import numpy as np
import os
from ultralytics import YOLO

class ClothingDetector:
    def __init__(self):
        # We use the base YOLOv8 nano model. 
        # Ultralytics will auto-download yolov8n.pt if not present.
        self.model_path = os.path.join("runs", "detect", "yolov8n.pt")
        try:
            self.model = YOLO('yolov8n.pt')
        except Exception as e:
            print(f"Failed to load YOLO model for clothing detection: {e}")
            self.model = None

    def extract_garments(self, img_array: np.ndarray) -> list:
        """
        Takes an image of a laundry basket and extracts individual clothing items using YOLOv8.
        Falls back to OpenCV contours if YOLO fails or detects nothing.
        """
        crops = []
        
        if self.model is not None:
            results = self.model(img_array, conf=0.15) # Low confidence to catch non-standard COCO objects like folded shirts
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    # Add padding
                    pad = 20
                    h, w = img_array.shape[:2]
                    x1 = max(0, x1 - pad)
                    y1 = max(0, y1 - pad)
                    x2 = min(w, x2 + pad)
                    y2 = min(h, y2 + pad)
                    
                    crop = img_array[y1:y2, x1:x2]
                    # Filter out tiny crops
                    if crop.shape[0] > 50 and crop.shape[1] > 50:
                        crops.append(crop)
                        
        if not crops:
            # Fallback to OpenCV Contour Detection
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            blurred = cv2.GaussianBlur(gray, (15, 15), 0)
            edges = cv2.Canny(blurred, 30, 150)
            kernel = np.ones((5,5), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=3)
            contours, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            h, w = img_array.shape[:2]
            min_area = (h * w) * 0.05
            
            for c in contours:
                area = cv2.contourArea(c)
                if area > min_area:
                    x, y, w_box, h_box = cv2.boundingRect(c)
                    pad = 20
                    x1 = max(0, x - pad)
                    y1 = max(0, y - pad)
                    x2 = min(w, x + w_box + pad)
                    y2 = min(h, y + h_box + pad)
                    crop = img_array[y1:y2, x1:x2]
                    crops.append(crop)
                    
        # If still nothing, return the whole image
        if not crops:
            crops.append(img_array)
            
        return crops

    def check_mixed_safety(self, items_results: list) -> str:
        """
        Takes a list of results from multiple garments and checks for washing conflicts.
        """
        has_whites = any(res['color'] == 'White' for res in items_results)
        has_darks = any(res['color'] in ['Black', 'Navy Blue', 'Dark Red'] for res in items_results)
        has_delicates = any(res['fabric'] in ['Silk', 'Wool'] for res in items_results)
        
        warnings = []
        if has_whites and has_darks:
            warnings.append("⚠️ **Color Bleed Risk:** You mixed dark colors with whites. Wash them separately!")
        if has_delicates:
            warnings.append("⚠️ **Delicate Fabric Detected:** Silk or Wool found in the basket. Use a gentle cycle or hand wash separately.")
            
        if warnings:
            return "\\n\\n".join(warnings)
        return "✅ **Safe to wash together.** No major conflicts detected."
