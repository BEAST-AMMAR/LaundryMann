# CODE SNIPPET 1: HSV Model Logic (utils.py)
import cv2
import numpy as np

# HSV ranges are empirical and tuned for general light/dark classification
# H (0-179), S (0-255), V (0-255) in OpenCV
HSV_RANGES = {
    # Dark: Low V (Brightness)
    "DARK": {
        "lower": np.array([0, 0, 0]), 
        "upper": np.array([179, 255, 70]) # V < 70 (Very Dark)
    },
    # Light: Low S (Saturation) and High V (Brightness)
    "LIGHT": {
        "lower": np.array([0, 0, 180]), # V > 180 (Very Bright)
        "upper": np.array([179, 60, 255]) # S < 60 (Low Saturation)
    },
    # Colored: High S and Mid V (Everything else with color)
    "COLORED": {
        "lower": np.array([0, 60, 70]), # S > 60 and V > 70
        "upper": np.array([179, 255, 180]) # V < 180 (Not too bright)
    }
}

def classify_hsv(image_path):
    # 1. Read and convert to HSV
    img_bgr = cv2.imread(image_path)
    if img_bgr is None: return "ERROR"
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    
    # Simple segmentation: assume a simple, clean background
    # We focus only on the pixels that are NOT background (e.g., using a fixed color background mask)
    # For a quick demo, we assume the whole image is the garment.

    max_score = 0
    predicted_class = "UNKNOWN"

    for name, limits in HSV_RANGES.items():
        # Create mask based on defined range
        mask = cv2.inRange(img_hsv, limits["lower"], limits["upper"])
        # Calculate the proportion of pixels in this range
        pixel_count = cv2.countNonZero(mask)
        proportion = pixel_count / (img_bgr.shape[0] * img_bgr.shape[1])
        
        if proportion > max_score:
            max_score = proportion
            predicted_class = name
            
    return predicted_class, max_score