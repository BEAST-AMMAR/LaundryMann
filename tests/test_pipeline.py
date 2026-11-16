"""
Comprehensive Test Suite for Nexus Laundry AI:
Validates Perception, Hardware Coordinates, Safety Bleed Logic, and Robotic Dispatch.
"""

import unittest
import numpy as np
import cv2

from src.models.color_classifier import ColorClassifier
from src.models.clothing_detector import ClothingDetector
from src.models.fabric_classifier import FabricClassifier
from src.models.ocr_reader import OCRReader
from src.core.decision_engine import LaundryDecisionEngine
from src.hardware.robot_controller import RoboticArmController
from src.hardware.sensor_interface import HardwareSensorInterface

class TestNexusPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.color_clf = ColorClassifier()
        cls.clothing_det = ClothingDetector()
        cls.fabric_clf = FabricClassifier()
        cls.ocr_reader = OCRReader()
        cls.decision_engine = LaundryDecisionEngine()
        cls.robot_arm = RoboticArmController()
        cls.sensors = HardwareSensorInterface()

    def test_color_classifier_white(self):
        # Create pure white image
        white_img = np.full((100, 100, 3), 250, dtype=np.uint8)
        profile = self.color_clf.analyze_color_profile(white_img)
        self.assertEqual(profile["category"], "LIGHT")
        self.assertIn("White", profile["color_name"])
        self.assertEqual(profile["bleed_risk"], "LOW")

    def test_color_classifier_dark_red(self):
        # Create dark red image: High Red, low Green, low Blue
        dark_red = np.zeros((100, 100, 3), dtype=np.uint8)
        dark_red[:, :, 0] = 130 # R
        dark_red[:, :, 1] = 10  # G
        dark_red[:, :, 2] = 15  # B
        profile = self.color_clf.analyze_color_profile(dark_red)
        self.assertIn(profile["category"], ["DARK", "COLORED"])
        self.assertEqual(profile["bleed_risk"], "HIGH")

    def test_color_bleed_warning_fires_on_mixed_whites_and_darks(self):
        """Validates that the safety warning fires when whites and bleeding darks are in the same batch."""
        mixed_batch = [
            {"color": "LIGHT", "color_name": "White", "bleed_risk": "LOW", "fabric": "Cotton"},
            {"color": "DARK", "color_name": "Dark Red", "bleed_risk": "HIGH", "fabric": "Cotton"}
        ]
        safety_report = self.clothing_det.check_mixed_safety(mixed_batch)
        self.assertIn("Color Bleed Hazard", safety_report)
        self.assertIn("Separate", safety_report)

    def test_delicate_warning_fires_on_silk_or_wool(self):
        batch = [
            {"color": "LIGHT", "color_name": "White", "fabric": "Silk"},
            {"color": "LIGHT", "color_name": "White", "fabric": "Cotton"}
        ]
        safety_report = self.clothing_det.check_mixed_safety(batch)
        self.assertIn("Delicate Fabric Alert", safety_report)

    def test_decision_engine_dry_clean_override(self):
        # If care label says dry clean only, route to Bin G
        res = self.decision_engine.decide_industrial_routing(
            color="LIGHT",
            fabric="Cotton",
            stains=[],
            ocr_constraints=["Dry Clean Only (Do Not Wash)"]
        )
        self.assertEqual(res["bin_id"], "BIN_G")
        self.assertIn("Dry Clean", res["reasons"][0])

    def test_decision_engine_odor_voc_hazard_override(self):
        # E-Nose VOC odor spike routes to Bin F
        res = self.decision_engine.decide_industrial_routing(
            color="LIGHT",
            fabric="Cotton",
            stains=[],
            odor_detected=True
        )
        self.assertEqual(res["bin_id"], "BIN_F")
        self.assertIn("Odor", res["bin_name"])

    def test_decision_engine_delicate_silk_routing(self):
        # Clean silk routes to Bin E
        res = self.decision_engine.decide_industrial_routing(
            color="LIGHT",
            fabric="Silk",
            stains=[]
        )
        self.assertEqual(res["bin_id"], "BIN_E")
        self.assertIn("Delicates", res["bin_name"])

    def test_decision_engine_stained_lights_to_bin_b(self):
        # Stained white item -> Bin B (Enzyme Pre-treat)
        res = self.decision_engine.decide_industrial_routing(
            color="LIGHT",
            fabric="Cotton",
            stains=[{"bbox": [10, 10, 50, 50], "confidence": 0.85}],
            color_name="White"
        )
        self.assertEqual(res["bin_id"], "BIN_B")
        self.assertIn("Heavy Enzyme", res["bin_name"])

    def test_robot_pixel_to_workspace_coordinates(self):
        # Center of 1280x720 camera frame should map to robot center
        rx, ry, rz = self.robot_arm.pixel_to_robot_coords(640, 360)
        self.assertEqual(rx, 320.0)
        self.assertEqual(ry, 0.0)
        self.assertEqual(rz, 25.0)

    def test_robot_grasp_parameters(self):
        bbox = [200, 150, 400, 350]
        params = self.robot_arm.compute_grasp_parameters(bbox, fabric="Silk")
        # Gentle grip for silk
        self.assertEqual(params["grip_force_n"], 4.5)
        self.assertIn("pick_coords_mm", params)

    def test_robot_pick_and_place_dispatch(self):
        bbox = [200, 150, 400, 350]
        packet = self.robot_arm.dispatch_pick_and_place(bbox, bin_id="BIN_A", fabric="Cotton")
        self.assertEqual(packet["target_bin"]["id"], "BIN_A")
        self.assertEqual(self.robot_arm.bin_counts["BIN_A"], 1)

if __name__ == "__main__":
    unittest.main()
