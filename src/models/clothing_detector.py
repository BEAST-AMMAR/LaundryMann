import cv2
import numpy as np
import os
from typing import List, Dict, Any, Tuple
from ultralytics import YOLO

class ClothingDetector:
    def __init__(self):
        # We use the YOLOv8 nano model for multi-item conveyor / basket detection.
        self.model_path = os.path.join("runs", "detect", "yolov8n.pt")
        try:
            self.model = YOLO('yolov8n.pt')
        except Exception as e:
            print(f"Failed to load YOLO model for clothing detection: {e}")
            self.model = None

    def extract_garments_with_metadata(self, img_array: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extracts individual garments from an inspection area or basket.
        Returns a list of dicts with crop, bounding box [x1, y1, x2, y2], and centroid (cx, cy).
        """
        garments = []
        h, w = img_array.shape[:2]

        if self.model is not None:
            results = self.model(img_array, conf=0.15, verbose=False)
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    # Add padding
                    pad = 20
                    x1 = max(0, x1 - pad)
                    y1 = max(0, y1 - pad)
                    x2 = min(w, x2 + pad)
                    y2 = min(h, y2 + pad)

                    crop = img_array[y1:y2, x1:x2]
                    # Filter out tiny crops
                    if crop.shape[0] > 50 and crop.shape[1] > 50:
                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)
                        garments.append({
                            "crop": crop,
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            "centroid": [cx, cy],
                            "area": int((x2 - x1) * (y2 - y1))
                        })

        if not garments:
            # Fallback to OpenCV Contour Detection
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            blurred = cv2.GaussianBlur(gray, (15, 15), 0)
            edges = cv2.Canny(blurred, 30, 150)
            kernel = np.ones((5, 5), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=3)
            contours, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    garments.append({
                        "crop": crop,
                        "bbox": [int(x1), int(y1), int(x2), int(y2)],
                        "centroid": [cx, cy],
                        "area": int(area)
                    })

        # If still nothing detected, treat the entire inspection frame as one garment
        if not garments:
            garments.append({
                "crop": img_array,
                "bbox": [0, 0, w, h],
                "centroid": [w // 2, h // 2],
                "area": w * h
            })

        return garments

    def extract_garments(self, img_array: np.ndarray) -> list:
        """
        Backward-compatible method returning only the cropped image arrays.
        """
        items = self.extract_garments_with_metadata(img_array)
        return [item["crop"] for item in items]

    def check_mixed_safety(self, items_results: list) -> str:
        """
        Checks a batch of detected items for cross-contamination risks:
        - Dye bleed risk (mixing Whites/Lights with Darks/Reds/Bleeders)
        - Mechanical fabric damage (mixing Silks/Wools with coarse Cottons/Denim)
        """
        def is_white_or_light(res: dict) -> bool:
            color = str(res.get("color", "")).upper()
            cname = str(res.get("color_name", "")).upper()
            return color == "LIGHT" or "WHITE" in cname or "CREAM" in cname or "LIGHT" in cname

        def is_dark_or_bleeder(res: dict) -> bool:
            color = str(res.get("color", "")).upper()
            cname = str(res.get("color_name", "")).upper()
            bleed = str(res.get("bleed_risk", "")).upper()
            return (
                color in ["DARK", "COLORED"]
                or bleed in ["HIGH", "HIGH_BLEED"]
                or any(k in cname for k in ["BLACK", "NAVY", "RED", "DARK", "PURPLE"])
            )

        def is_delicate(res: dict) -> bool:
            fabric = str(res.get("fabric", "")).upper()
            return any(k in fabric for k in ["SILK", "WOOL", "LACE", "CASHMERE", "DELICATE"])

        has_whites = any(is_white_or_light(r) for r in items_results)
        has_darks = any(is_dark_or_bleeder(r) for r in items_results)
        has_delicates = any(is_delicate(r) for r in items_results)

        warnings = []
        if has_whites and has_darks:
            warnings.append("⚠️ **Color Bleed Hazard:** Mixed White/Light items detected with Dark/Bleeding items. Separate into Load 1 (Whites) and Load 2 (Darks) to prevent dye transfer.")
        
        if has_delicates:
            warnings.append("⚠️ **Delicate Fabric Alert:** Silk or Wool detected in the batch. Do not wash with rough cottons/denim. Route to Bin E (Delicates - Cold Gentle).")

        if warnings:
            return "\n\n".join(warnings)
        return "✅ **Safe Batch:** All items are compatible in the same wash load. No dye bleed or fabric friction hazard detected."
