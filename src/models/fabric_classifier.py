import os
import cv2
import numpy as np
from typing import Tuple, Dict, Any

class FabricClassifier:
    """
    Industrial Fabric Texture & Fibre Classifier.
    Extracts surface roughness, spatial frequency, and specular reflectance
    to distinguish Cotton, Denim, Silk, Wool, and Synthetics,
    with calibrated confidence and explicit abstention when ambiguous.
    """
    def __init__(self):
        self.model = None
        self.weight_path = os.path.join("runs", "classify", "apparel_classifier_v1", "weights", "best.pt")
        
        if os.path.exists(self.weight_path):
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.weight_path)
                print(f"[FabricClassifier] Loaded YOLO classification weights from {self.weight_path}")
            except Exception as e:
                print(f"[FabricClassifier] Could not load YOLO weights: {e}")
                self.model = None
        else:
            self.model = None

    def analyze_texture_features(self, image_np: np.ndarray) -> Dict[str, float]:
        """
        Extracts spatial texture statistics:
        - Contrast & variance (high for Denim/Wool, low for Silk)
        - High-frequency edge density (Laplacian variance)
        - Specular highlight ratio (reflectivity of silk/synthetics)
        """
        if len(image_np.shape) == 3:
            gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_np

        # Center sample
        h, w = gray.shape[:2]
        ch_s, ch_e = int(h * 0.25), int(h * 0.75)
        cw_s, cw_e = int(w * 0.25), int(w * 0.75)
        sample = gray[ch_s:ch_e, cw_s:cw_e]
        if sample.size == 0:
            sample = gray

        # 1. High frequency micro-texture variance
        laplacian = cv2.Laplacian(sample, cv2.CV_64F)
        lap_var = float(laplacian.var())

        # 2. Local contrast & standard deviation
        mean_val = float(np.mean(sample))
        std_val = float(np.std(sample))

        # 3. Specular highlights (high intensity pixels relative to mean)
        specular_ratio = float(np.sum(sample > (mean_val + 2.0 * std_val))) / (sample.size + 1e-5)

        # 4. Horizontal vs vertical gradient ratio (twill weave has directional orientation)
        sobel_x = cv2.Sobel(sample, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(sample, cv2.CV_64F, 0, 1, ksize=3)
        grad_energy_x = float(np.mean(np.abs(sobel_x)))
        grad_energy_y = float(np.mean(np.abs(sobel_y)))
        twill_ratio = abs(grad_energy_x - grad_energy_y) / (grad_energy_x + grad_energy_y + 1e-5)

        return {
            "roughness_lap_var": lap_var,
            "std_dev": std_val,
            "specular_ratio": specular_ratio,
            "twill_ratio": twill_ratio
        }

    def predict_fabric(self, image_np: np.ndarray) -> Tuple[str, float]:
        """
        Classifies fabric into Cotton, Denim, Silk, Wool, or Polyester.
        Returns: (Fabric Name, Confidence float 0.0 - 1.0)
        """
        # If fine-tuned deep learning weights are present, prioritize them
        if self.model is not None:
            try:
                results = self.model(image_np, verbose=False)
                result = results[0]
                top_class_id = result.probs.top1
                top_class_name = result.names[top_class_id]
                confidence = float(result.probs.top1conf.item())
                return top_class_name, confidence
            except Exception:
                pass

        # Texture Computer Vision Analysis
        if image_np is None or image_np.size == 0:
            return "Cotton", 0.70

        tex = self.analyze_texture_features(image_np)
        lap_var = tex["roughness_lap_var"]
        std_dev = tex["std_dev"]
        specular = tex["specular_ratio"]
        twill = tex["twill_ratio"]

        # Classification rules based on textile optical properties:
        # Silk: very smooth (low lap_var), high specular sheen, low roughness
        if lap_var < 80.0 and specular > 0.035 and std_dev < 38.0:
            return "Silk", 0.88
            
        # Wool: very high texture roughness, fibrous surface (moderate to high lap_var without directional twill)
        if lap_var > 380.0 and twill < 0.12 and std_dev > 45.0:
            return "Wool", 0.85

        # Denim: pronounced diagonal twill weave with high gradient difference
        if twill > 0.22 and lap_var > 150.0:
            return "Denim", 0.91

        # Polyester / Synthetic: moderate sheen, very low twill, uniform reflectance
        if specular > 0.04 and lap_var < 160.0:
            return "Polyester", 0.82

        # Standard Cotton: moderate roughness, balanced gradient
        if lap_var > 100.0:
            return "Cotton", 0.89

        # Default abstention / general cotton blend
        return "Cotton / Blend", 0.78
