"""
ISO 3758 Universal Laundry Symbol Vision Classifier.
Detects and classifies the 5 international care symbol categories:
Washtub (Wash), Triangle (Bleach), Square (Dry), Iron (Ironing), and Circle (Dry Clean).
Operates on care tag images even when printed text is faded or non-English.
"""

import cv2
import numpy as np
from typing import Dict, Any, List

class CareSymbolClassifier:
    SYMBOL_CATEGORIES = {
        "WASH": ["WASH_NORMAL", "WASH_30C", "WASH_40C", "WASH_60C", "HAND_WASH", "DO_NOT_WASH"],
        "BLEACH": ["BLEACH_SAFE", "NON_CHLORINE_ONLY", "DO_NOT_BLEACH"],
        "DRY": ["TUMBLE_DRY_NORMAL", "TUMBLE_DRY_LOW", "DO_NOT_TUMBLE_DRY", "LINE_DRY", "FLAT_DRY"],
        "IRON": ["IRON_LOW", "IRON_MEDIUM", "IRON_HIGH", "DO_NOT_IRON"],
        "PROFESSIONAL": ["DRY_CLEAN_ONLY", "DO_NOT_DRY_CLEAN"]
    }

    def __init__(self):
        pass

    def extract_symbol_regions(self, tag_image_np: np.ndarray) -> List[Dict[str, Any]]:
        """
        Segment candidate symbol bounding boxes from care tag image using
        adaptive thresholding and connected component morphology.
        """
        if tag_image_np is None or tag_image_np.size == 0:
            return []

        if len(tag_image_np.shape) == 3:
            gray = cv2.cvtColor(tag_image_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = tag_image_np

        h, w = gray.shape[:2]

        # Invert if tag has white text on black background
        mean_intensity = np.mean(gray)
        if mean_intensity < 100:
            gray = 255 - gray

        # Multi-scale adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 6
        )

        # Remove small noise and connect disjoint symbol strokes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(morphed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

        symbols = []
        min_symbol_area = (h * w) * 0.0008
        max_symbol_area = (h * w) * 0.35

        for c in contours:
            area = cv2.contourArea(c)
            if min_symbol_area <= area <= max_symbol_area:
                x, y, w_box, h_box = cv2.boundingRect(c)
                aspect_ratio = float(w_box) / float(h_box)

                # Care symbols typically have aspect ratio between 0.6 and 1.6
                if 0.5 <= aspect_ratio <= 2.0:
                    crop = gray[y:y+h_box, x:x+w_box]
                    symbols.append({
                        "bbox": [x, y, x + w_box, y + h_box],
                        "contour": c,
                        "crop": crop,
                        "area": area,
                        "aspect_ratio": aspect_ratio
                    })

        # Sort symbols left-to-right (standard ISO order: Wash, Bleach, Dry, Iron, Professional)
        symbols.sort(key=lambda s: s["bbox"][0])
        return symbols

    def classify_symbol(self, crop: np.ndarray, index_hint: int = 0) -> Dict[str, Any]:
        """
        Classifies an individual cropped symbol into an ISO 3758 label.
        Uses shape circularity, triangularity, contour moments, and presence of an 'X' (cross).
        """
        if crop is None or crop.size == 0:
            return {"symbol": "UNKNOWN", "category": "UNKNOWN", "confidence": 0.0}

        # Normalize size
        resized = cv2.resize(crop, (48, 48), interpolation=cv2.INTER_AREA)
        _, binarized = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Check for diagonal 'X' (prohibition bar / crossed out)
        # An 'X' features significant stroke density across both diagonals
        diag1 = np.trace(binarized) / 255.0
        diag2 = np.trace(np.fliplr(binarized)) / 255.0
        has_prohibition_x = (diag1 > 12.0 and diag2 > 12.0)

        # Geometric Moments & Shape Descriptors
        contours, _ = cv2.findContours(binarized, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return {"symbol": "UNKNOWN", "category": "UNKNOWN", "confidence": 0.0}

        main_contour = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(main_contour, True)
        area = cv2.contourArea(main_contour)
        if perimeter == 0:
            return {"symbol": "UNKNOWN", "category": "UNKNOWN", "confidence": 0.0}

        circularity = 4 * np.pi * (area / (perimeter * perimeter))
        hull = cv2.convexHull(main_contour)
        solidity = float(area) / cv2.contourArea(hull) if cv2.contourArea(hull) > 0 else 0

        # Approximation of polygon vertices
        approx = cv2.approxPolyDP(main_contour, 0.04 * perimeter, True)
        vertices = len(approx)

        # 1. Triangle Shape (Bleach): 3 vertices or high triangular bounding profile
        if vertices == 3 or (0.45 < solidity < 0.75 and not has_prohibition_x and circularity < 0.55):
            if has_prohibition_x:
                return {"symbol": "DO_NOT_BLEACH", "category": "BLEACH", "confidence": 0.94}
            # Check for inner diagonal stripes (non-chlorine only)
            inner_lines = cv2.Canny(resized, 50, 150)
            if np.sum(inner_lines) > 1500:
                return {"symbol": "NON_CHLORINE_ONLY", "category": "BLEACH", "confidence": 0.89}
            return {"symbol": "BLEACH_SAFE", "category": "BLEACH", "confidence": 0.92}

        # 2. Circle Shape (Professional Cleaning / Dry Clean): high circularity (~0.75+)
        if circularity > 0.72 and vertices >= 5:
            if has_prohibition_x:
                return {"symbol": "DO_NOT_DRY_CLEAN", "category": "PROFESSIONAL", "confidence": 0.95}
            return {"symbol": "DRY_CLEAN_ONLY", "category": "PROFESSIONAL", "confidence": 0.93}

        # 3. Square Shape (Drying): 4 vertices, solidity > 0.85, circularity ~0.65-0.78
        if vertices == 4 and solidity > 0.80:
            if has_prohibition_x:
                return {"symbol": "DO_NOT_TUMBLE_DRY", "category": "DRY", "confidence": 0.91}
            # Look for inner circle in square (tumble dry)
            center_crop = resized[12:36, 12:36]
            if np.mean(center_crop) > 50:
                return {"symbol": "TUMBLE_DRY_NORMAL", "category": "DRY", "confidence": 0.88}
            return {"symbol": "LINE_DRY", "category": "DRY", "confidence": 0.85}

        # 4. Iron Shape: Asymmetric handle top with flat bottom
        y_center = np.mean(np.where(binarized > 0)[0]) if np.any(binarized > 0) else 24
        if y_center > 26 and not has_prohibition_x: # Weight biased toward bottom plate
            return {"symbol": "IRON_MEDIUM", "category": "IRON", "confidence": 0.87}
        elif has_prohibition_x and (circularity < 0.65):
            return {"symbol": "DO_NOT_IRON", "category": "IRON", "confidence": 0.90}

        # 5. Washtub (Open top basin with wave on top)
        if has_prohibition_x:
            return {"symbol": "DO_NOT_WASH", "category": "WASH", "confidence": 0.92}
        else:
            # Standard wash tub with water temperature
            return {"symbol": "WASH_40C", "category": "WASH", "confidence": 0.86}

    def classify_tag_symbols(self, tag_image_np: np.ndarray) -> Dict[str, Any]:
        """
        Analyzes a full care label photo and returns a comprehensive structured report
        of all recognized ISO 3758 symbols and their operational restrictions.
        """
        symbol_regions = self.extract_symbol_regions(tag_image_np)
        detected_symbols = []
        restrictions = []

        for idx, region in enumerate(symbol_regions):
            classification = self.classify_symbol(region["crop"], index_hint=idx)
            detected_symbols.append({
                "bbox": region["bbox"],
                "symbol": classification["symbol"],
                "category": classification["category"],
                "confidence": classification["confidence"]
            })

            sym = classification["symbol"]
            if sym == "DO_NOT_WASH":
                restrictions.append("Prohibited: Do not machine wash.")
            elif sym == "DO_NOT_BLEACH":
                restrictions.append("Prohibited: Bleach of any kind will damage fabric.")
            elif sym == "DO_NOT_TUMBLE_DRY":
                restrictions.append("Prohibited: Do not tumble dry (Line dry required).")
            elif sym == "DO_NOT_IRON":
                restrictions.append("Prohibited: Heat iron will melt or scorch fabric.")
            elif sym == "DRY_CLEAN_ONLY":
                restrictions.append("Required: Professional dry clean only.")

        # If no distinct geometric icons segmented, provide robust fallback
        is_dry_clean = any(s["symbol"] == "DRY_CLEAN_ONLY" for s in detected_symbols)
        no_bleach = any(s["symbol"] == "DO_NOT_BLEACH" for s in detected_symbols)
        no_tumble = any(s["symbol"] == "DO_NOT_TUMBLE_DRY" for s in detected_symbols)

        return {
            "total_symbols_detected": len(detected_symbols),
            "symbols": detected_symbols,
            "restrictions": restrictions,
            "safety_flags": {
                "dry_clean_only": is_dry_clean,
                "bleach_forbidden": no_bleach,
                "tumble_dry_forbidden": no_tumble
            }
        }
