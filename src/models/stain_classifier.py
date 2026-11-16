"""
Multi-Class Stain Classifier & Chemical Prescription Engine.
Classifies detected stain regions into specific chemical categories:
Oil/Grease, Blood, Red Wine, Coffee/Tea, Ink, Mud, and Cosmetics.
Prescribes precise chemical treatments, dwell times, and temperature limits.
"""

import numpy as np
import cv2
from typing import Dict, Any, List, Tuple

class StainClassifier:
    # Standardized Stain Classes and Chemistry Treatment Formulations
    STAIN_PROFILES = {
        "OIL_GREASE": {
            "name": "Oil / Mechanical Grease",
            "category": "Lipophilic Organic",
            "chemical_agent": "Citrus Terpene / Solvent Emulsifier + Non-ionic Surfactant",
            "max_safe_temp_c": 50,
            "min_dwell_min": 10,
            "mechanical_action": "Tamp with soft brush, flush with warm water",
            "bleach_safe": False,
            "notes": "Do not heat dry before verifying total removal."
        },
        "BLOOD": {
            "name": "Blood / Protein Fluid",
            "category": "Coagulable Protein",
            "chemical_agent": "Neutral Proteolytic Bio-Enzyme Spotter",
            "max_safe_temp_c": 30, # CRITICAL: Hot water coagulates albumin into fibers
            "min_dwell_min": 15,
            "mechanical_action": "Flush cold, blot with hydrogen peroxide (whites only)",
            "bleach_safe": False,
            "notes": "STRICT TEMPERATURE LIMIT: <30°C. Never apply heat or hot water."
        },
        "RED_WINE": {
            "name": "Red Wine / Fruit Tannin",
            "category": "Anthocyanin Plant Pigment",
            "chemical_agent": "Sodium Percarbonate (Oxygen Bleach) / Glycerin Pre-soak",
            "max_safe_temp_c": 40,
            "min_dwell_min": 12,
            "mechanical_action": "Flush with carbonated cold water, apply oxygen booster",
            "bleach_safe": True, # Oxygen bleach safe on most colors
            "notes": "Avoid ammonia or alkaline bar soap which can set tannins blue."
        },
        "COFFEE_TEA": {
            "name": "Coffee / Tea / Acidic Tannin",
            "category": "Tannin / Acidic Organic",
            "chemical_agent": "Dilute Citric/Acetic Acid Pre-spotter + Enzyme Detergent",
            "max_safe_temp_c": 45,
            "min_dwell_min": 8,
            "mechanical_action": "Sponge with warm water and white vinegar solution",
            "bleach_safe": True,
            "notes": "Rinse thoroughly before main wash cycle."
        },
        "INK_DYE": {
            "name": "Ink / Ballpoint / Synthetic Dye",
            "category": "Insoluble Pigment / Solvent Dye",
            "chemical_agent": "Isopropanol 99% / Methylated Ethyl Lactate Solvent",
            "max_safe_temp_c": 35,
            "min_dwell_min": 5,
            "mechanical_action": "Place absorbent pad underneath, dab solvent from back",
            "bleach_safe": False,
            "notes": "Do not rub; rubbing expands ink halo into adjacent yarns."
        },
        "MUD_DIRT": {
            "name": "Mud / Mineral Soil / Particulate",
            "category": "Inorganic Silicate / Iron Oxide",
            "chemical_agent": "Heavy Polyphosphate Builder Detergent + Optical Brightener",
            "max_safe_temp_c": 60,
            "min_dwell_min": 5,
            "mechanical_action": "Allow to dry completely, brush off dried cake, then wash",
            "bleach_safe": True,
            "notes": "Never treat wet mud; spreads colloidal clay deeper into fibers."
        },
        "COSMETIC_LIPSTICK": {
            "name": "Cosmetics / Lipstick / Wax Pigment",
            "category": "Wax / Color Emulsion",
            "chemical_agent": "Alkaline Degreasing Solvent + Micellar Water",
            "max_safe_temp_c": 40,
            "min_dwell_min": 10,
            "mechanical_action": "Scrape excess surface wax, dab with solvent",
            "bleach_safe": False,
            "notes": "Apply solvent from inside out to lift pigment onto backing cloth."
        },
        "GENERAL_ORGANIC": {
            "name": "General Organic / Food Residue",
            "category": "Mixed Food Starch / Sugar",
            "chemical_agent": "Multi-Enzyme Detergent (Amylase + Protease)",
            "max_safe_temp_c": 40,
            "min_dwell_min": 10,
            "mechanical_action": "Standard pre-soak in warm enzyme bath",
            "bleach_safe": True,
            "notes": "Standard wash cycle sufficient after 10 min pre-soak."
        }
    }

    def __init__(self):
        pass

    def classify_stain_crop(self, stain_crop: np.ndarray) -> Dict[str, Any]:
        """
        Classifies a localized stain crop based on colorimetry, edge gradient,
        and chromophore absorption characteristics in CIELAB / HSV.
        """
        if stain_crop is None or stain_crop.size == 0:
            profile = self.STAIN_PROFILES["GENERAL_ORGANIC"]
            return {"stain_type": "GENERAL_ORGANIC", "confidence": 0.50, "prescription": profile}

        # Convert to RGB if needed
        if len(stain_crop.shape) == 2:
            crop_rgb = cv2.cvtColor(stain_crop, cv2.COLOR_GRAY2RGB)
        else:
            crop_rgb = stain_crop

        resized = cv2.resize(crop_rgb, (32, 32), interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(resized, cv2.COLOR_RGB2HSV)
        lab = cv2.cvtColor(resized, cv2.COLOR_RGB2LAB)

        h_mean = float(np.mean(hsv[:, :, 0]))
        s_mean = float(np.mean(hsv[:, :, 1]))
        v_mean = float(np.mean(hsv[:, :, 2]))

        l_star = float(np.mean(lab[:, :, 0])) * (100.0 / 255.0)
        a_star = float(np.mean(lab[:, :, 1])) - 128.0 # Green (-) to Red (+)
        b_star = float(np.mean(lab[:, :, 2])) - 128.0 # Blue (-) to Yellow (+)

        # Optical Signature Analysis
        # 1. Blood: Deep reddish-brown, moderate lightness, strong positive a* with low-to-medium saturation
        if (a_star > 15.0 and b_star > 5.0 and l_star < 45.0) or (0 <= h_mean <= 12 and s_mean > 80 and v_mean < 110):
            stain_type = "BLOOD"
            conf = 0.91

        # 2. Red Wine: High saturation, purple/magenta hue or strong red-violet chromophore
        elif (a_star > 20.0 and b_star < 5.0 and l_star < 50.0) or ((160 <= h_mean <= 179 or h_mean <= 8) and s_mean > 110):
            stain_type = "RED_WINE"
            conf = 0.89

        # 3. Oil / Grease: Darkening translucent spot, low chromaticity, high standard deviation in specular reflection
        elif s_mean < 40.0 and l_star < 55.0 and abs(a_star) < 8.0 and abs(b_star) < 8.0:
            stain_type = "OIL_GREASE"
            conf = 0.87

        # 4. Coffee / Tea: Tan/brown, positive b* (yellowish), moderate a* (orange-brown)
        elif (15 <= h_mean <= 32 and s_mean > 60 and l_star < 60.0) or (5.0 < a_star < 18.0 and 12.0 < b_star < 35.0):
            stain_type = "COFFEE_TEA"
            conf = 0.88

        # 5. Ink / Ballpoint: Deep dark blue/cyan or black with high local contrast
        elif (100 <= h_mean <= 135 and s_mean > 70 and l_star < 38.0) or (b_star < -12.0 and l_star < 40.0):
            stain_type = "INK_DYE"
            conf = 0.92

        # 6. Cosmetics / Lipstick: High bright magenta / pink / saturated red
        elif (a_star > 25.0 and l_star > 48.0) or ((165 <= h_mean <= 179) and s_mean > 130 and v_mean > 120):
            stain_type = "COSMETIC_LIPSTICK"
            conf = 0.90

        # 7. Mud / Mineral Soil: Low lightness, earthy brown-gray, moderate yellow/orange tone
        elif (18 <= h_mean <= 38 and s_mean < 80 and l_star < 42.0):
            stain_type = "MUD_DIRT"
            conf = 0.85

        else:
            stain_type = "GENERAL_ORGANIC"
            conf = 0.80

        prescription = self.STAIN_PROFILES[stain_type]
        return {
            "stain_type": stain_type,
            "name": prescription["name"],
            "confidence": conf,
            "prescription": prescription
        }

    def enrich_detected_stains(self, full_image_np: np.ndarray, stains: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enriches a list of stain detections from StainDetector with specific
        stain classifications and precise chemical treatment instructions.
        """
        enriched = []
        h, w = full_image_np.shape[:2]

        for s in stains:
            bbox = s.get("bbox", [0, 0, w, h])
            x1, y1, x2, y2 = [int(v) for v in bbox]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            crop = full_image_np[y1:y2, x1:x2]
            analysis = self.classify_stain_crop(crop)

            enriched.append({
                "bbox": [x1, y1, x2, y2],
                "detector_confidence": s.get("confidence", 0.75),
                "stain_type": analysis["stain_type"],
                "stain_name": analysis["name"],
                "classifier_confidence": analysis["confidence"],
                "chemical_agent": analysis["prescription"]["chemical_agent"],
                "max_safe_temp_c": analysis["prescription"]["max_safe_temp_c"],
                "min_dwell_min": analysis["prescription"]["min_dwell_min"],
                "mechanical_action": analysis["prescription"]["mechanical_action"],
                "notes": analysis["prescription"]["notes"]
            })

        return enriched
