import cv2
import numpy as np
import re
from typing import List, Dict, Any

class OCRReader:
    """
    Care Label Tag Reader and ISO 3758 Constraint Parser.
    Extracts washing limits, bleaching rules, drying constraints,
    and fiber composition from physical care labels.
    """
    def __init__(self):
        # Check if tesseract is available
        self.tesseract_available = False
        try:
            import pytesseract
            self.pytesseract = pytesseract
            # Test invocation
            _ = pytesseract.get_tesseract_version()
            self.tesseract_available = True
        except Exception:
            # Common Windows fallback paths
            win_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
            ]
            import os
            for wp in win_paths:
                if os.path.exists(wp):
                    try:
                        import pytesseract
                        pytesseract.pytesseract.tesseract_cmd = wp
                        self.pytesseract = pytesseract
                        self.tesseract_available = True
                        break
                    except Exception:
                        pass

    def read_care_label(self, img_array: np.ndarray) -> str:
        """
        Reads raw text from a care label image with multi-pass image enhancement.
        """
        if not self.tesseract_available or img_array is None or img_array.size == 0:
            return ""

        try:
            # Grayscale conversion
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Resize to ensure sufficient DPI for OCR
            h, w = gray.shape[:2]
            if h < 400 or w < 400:
                scale = max(2.0, 600.0 / max(h, w))
                gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

            # Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            contrast = clahe.apply(gray)

            # Adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 4
            )

            custom_config = r'--oem 3 --psm 6'
            text = self.pytesseract.image_to_string(thresh, config=custom_config)
            return text.strip().lower()
        except Exception as e:
            print(f"[OCRReader] Warning: OCR extraction error: {e}")
            return ""

    def parse_care_instructions(self, text: str) -> List[str]:
        """
        Parses OCR text for standardized care requirements and hard constraints.
        """
        instructions = []
        if not text:
            return instructions

        clean = text.lower()

        # Temperature constraints
        if any(k in clean for k in ["cold", "30c", "30°c", "85f"]):
            instructions.append("Machine Wash Cold (30°C)")
        elif any(k in clean for k in ["warm", "40c", "40°c", "105f"]):
            instructions.append("Machine Wash Warm (40°C)")
        elif any(k in clean for k in ["hot", "60c", "60°c", "140f"]):
            instructions.append("Machine Wash Hot (60°C)")

        # Cycle / Wash Type
        if "hand wash" in clean:
            instructions.append("Hand Wash Only")
        if "gentle" in clean or "delicate" in clean:
            instructions.append("Gentle Cycle Required")
        if "wash separately" in clean or "wash with like colors" in clean:
            instructions.append("Wash Separately (High Bleed Risk)")

        # Bleaching
        if any(k in clean for k in ["do not bleach", "no bleach", "non-chlorine"]):
            instructions.append("Do Not Bleach")
        elif "bleach" in clean and "no" not in clean:
            instructions.append("Bleach Safe")

        # Drying
        if any(k in clean for k in ["do not tumble dry", "line dry", "hang dry"]):
            instructions.append("Line Dry / Do Not Tumble Dry")
        elif "flat dry" in clean:
            instructions.append("Dry Flat in Shade")
        elif "tumble dry low" in clean:
            instructions.append("Tumble Dry Low Heat")

        # Professional Care
        if "dry clean only" in clean:
            instructions.append("Dry Clean Only (Do Not Wash)")

        # Fiber composition detection
        fibers = []
        for fiber in ["cotton", "silk", "wool", "polyester", "linen", "viscose", "spandex", "nylon"]:
            if fiber in clean:
                fibers.append(fiber.capitalize())
        if fibers:
            instructions.append(f"Detected Fiber: {', '.join(fibers)}")

        return instructions

    def extract_structured_tag(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        Extracts structured constraints object for the decision engine.
        """
        raw_text = self.read_care_label(img_array)
        parsed = self.parse_care_instructions(raw_text)

        return {
            "raw_text": raw_text,
            "parsed_instructions": parsed,
            "is_dry_clean_only": any("dry clean" in p.lower() for p in parsed),
            "is_hand_wash_only": any("hand wash" in p.lower() for p in parsed),
            "bleach_forbidden": any("do not bleach" in p.lower() for p in parsed),
            "line_dry_required": any("line dry" in p.lower() for p in parsed)
        }
