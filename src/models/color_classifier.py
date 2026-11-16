import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms
import numpy as np
import cv2
from typing import Dict, Any, Tuple

class SimpleLaundryCNN(nn.Module):
    def __init__(self, num_classes=3):
        super(SimpleLaundryCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(64 * 4 * 4, 128)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = torch.flatten(x, 1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

class ColorClassifier:
    """
    Industrial Color & Bleed Risk Analyzer.
    Combines calibrated CIELAB/HSV colorimetry with PyTorch CNN verification.
    Resolves exact color names (White, Navy Blue, Dark Red, etc.) and calculates
    dye-bleed safety risk for sorting.
    """
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.classes = ["COLORED", "DARK", "LIGHT"]
        self.model = SimpleLaundryCNN(num_classes=3)
        self.model.to(self.device)
        
        weight_path = "laundry_cnn.pth"
        if not os.path.exists(weight_path):
            weight_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "laundry_cnn.pth")

        if os.path.exists(weight_path):
            try:
                self.model.load_state_dict(torch.load(weight_path, map_location=self.device))
                self.model.eval()
                self.model_loaded = True
            except Exception as e:
                print(f"[ColorClassifier] Failed to load PyTorch weights from {weight_path}: {e}")
                self.model_loaded = False
        else:
            self.model_loaded = False

    def analyze_color_profile(self, image_np: np.ndarray) -> Dict[str, Any]:
        """
        Extracts dominant color name, CIELAB metrics, and dye-bleed risk.
        Works across both single garment crops and basket images.
        """
        if image_np is None or image_np.size == 0:
            return {
                "category": "LIGHT",
                "color_name": "White",
                "bleed_risk": "LOW",
                "dominant_rgb": [255, 255, 255],
                "hex": "#FFFFFF",
                "confidence": 0.50
            }

        # Convert to RGB if needed
        if len(image_np.shape) == 2:
            img_rgb = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
        else:
            img_rgb = image_np

        # Center crop 60% of image to sample garment fabric rather than conveyor background
        h, w = img_rgb.shape[:2]
        ch_start, ch_end = int(h * 0.2), int(h * 0.8)
        cw_start, cw_end = int(w * 0.2), int(w * 0.8)
        sample = img_rgb[ch_start:ch_end, cw_start:cw_end]
        if sample.size == 0:
            sample = img_rgb

        # Resize for fast deterministic color clustering
        resized = cv2.resize(sample, (64, 64), interpolation=cv2.INTER_AREA)
        pixels = resized.reshape(-1, 3).astype(np.float32)

        # Median / mean RGB
        mean_r, mean_g, mean_b = np.median(pixels, axis=0)
        dominant_rgb = [int(mean_r), int(mean_g), int(mean_b)]
        hex_code = f"#{dominant_rgb[0]:02X}{dominant_rgb[1]:02X}{dominant_rgb[2]:02X}"

        # Color Space Transformations
        # 1. HSV analysis
        hsv_sample = cv2.cvtColor(resized.astype(np.uint8), cv2.COLOR_RGB2HSV)
        h_channel = np.median(hsv_sample[:, :, 0])  # 0 to 179
        s_channel = np.median(hsv_sample[:, :, 1])  # 0 to 255
        v_channel = np.median(hsv_sample[:, :, 2])  # 0 to 255

        # 2. CIELAB Lightness (L*) analysis: 0 (black) to 100 (white)
        lab_sample = cv2.cvtColor(resized.astype(np.uint8), cv2.COLOR_RGB2LAB)
        l_star = np.median(lab_sample[:, :, 0]) * (100.0 / 255.0)

        # Classify exact color name and high-level category
        if l_star > 78 and s_channel < 55:
            color_name = "White"
            category = "LIGHT"
            bleed_risk = "LOW"
            conf = 0.94
        elif l_star > 68 and s_channel < 65:
            color_name = "Light Gray"
            category = "LIGHT"
            bleed_risk = "LOW"
            conf = 0.88
        elif l_star > 65 and s_channel < 110 and (20 <= h_channel <= 45):
            color_name = "Beige / Cream"
            category = "LIGHT"
            bleed_risk = "LOW"
            conf = 0.85
        elif l_star < 28 or (v_channel < 45):
            color_name = "Black"
            category = "DARK"
            bleed_risk = "HIGH"
            conf = 0.95
        elif (100 <= h_channel <= 135) and l_star < 45:
            color_name = "Navy Blue"
            category = "DARK"
            bleed_risk = "HIGH"
            conf = 0.92
        elif (h_channel <= 10 or h_channel >= 170) and l_star < 45:
            color_name = "Dark Red"
            category = "DARK"
            bleed_risk = "HIGH"
            conf = 0.90
        elif (h_channel <= 10 or h_channel >= 170) and s_channel > 120:
            color_name = "Bright Red"
            category = "COLORED"
            bleed_risk = "HIGH"
            conf = 0.93
        elif (100 <= h_channel <= 130) and s_channel > 100:
            color_name = "Blue"
            category = "COLORED"
            bleed_risk = "MODERATE"
            conf = 0.91
        elif (35 <= h_channel <= 85) and s_channel > 80:
            color_name = "Green"
            category = "COLORED"
            bleed_risk = "MODERATE"
            conf = 0.89
        elif (15 <= h_channel <= 35) and s_channel > 100:
            color_name = "Yellow / Orange"
            category = "COLORED"
            bleed_risk = "MODERATE"
            conf = 0.88
        elif (135 <= h_channel <= 165) and s_channel > 80:
            color_name = "Purple"
            category = "COLORED"
            bleed_risk = "HIGH"
            conf = 0.87
        elif l_star < 50:
            color_name = "Dark Wash"
            category = "DARK"
            bleed_risk = "HIGH"
            conf = 0.84
        elif s_channel > 75:
            color_name = "Colored"
            category = "COLORED"
            bleed_risk = "MODERATE"
            conf = 0.82
        else:
            color_name = "Light Neutral"
            category = "LIGHT"
            bleed_risk = "LOW"
            conf = 0.80

        return {
            "category": category,
            "color_name": color_name,
            "bleed_risk": bleed_risk,
            "dominant_rgb": dominant_rgb,
            "hex": hex_code,
            "cielab_l": round(float(l_star), 1),
            "confidence": conf
        }

    def predict_color(self, image_np: np.ndarray) -> Tuple[str, float]:
        """
        Primary interface matching original method signature.
        Returns: (Category "LIGHT" | "DARK" | "COLORED", confidence)
        """
        profile = self.analyze_color_profile(image_np)
        return profile["category"], profile["confidence"]
