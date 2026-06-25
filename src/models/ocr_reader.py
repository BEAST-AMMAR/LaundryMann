import pytesseract
import cv2
import numpy as np

class OCRReader:
    def __init__(self):
        # Configure tesseract cmd if needed, generally it must be in PATH on Windows
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
        
    def read_care_label(self, img_array: np.ndarray) -> str:
        """
        Reads text from a care label image using Tesseract OCR.
        Preprocesses the image for better contrast.
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Apply adaptive thresholding to highlight text
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Extract text
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(thresh, config=custom_config)
            return text.strip().lower()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def parse_care_instructions(self, text: str) -> list:
        """
        Parses OCR text for common laundry keywords.
        Returns a list of hard constraints to append to the decision engine.
        """
        instructions = []
        if not text:
            return instructions
            
        if "cold" in text or "30c" in text:
            instructions.append("Machine Wash Cold")
        if "hand wash" in text:
            instructions.append("Hand Wash Only")
        if "do not bleach" in text or "no bleach" in text:
            instructions.append("Do Not Bleach")
        if "tumble dry low" in text:
            instructions.append("Tumble Dry Low")
        if "do not tumble dry" in text or "line dry" in text:
            instructions.append("Line Dry")
        if "dry clean only" in text:
            instructions.append("Dry Clean Only")
            
        return instructions
