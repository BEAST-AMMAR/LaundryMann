"""
Automated Test Suite for Advanced AI Vision, Smart Factory Operations,
Security Input Validation, and Safety Guardrails.
"""

import unittest
import numpy as np
import io
from PIL import Image

from src.models.stain_classifier import StainClassifier
from src.models.care_symbol_classifier import CareSymbolClassifier
from src.core.load_balancer import WorkcellLoadBalancer
from src.core.sustainability import SustainabilityEngine
from src.security.input_validator import SecurityValidator
from src.security.guardrails import SafetyGuardrails
from src.hardware.multi_camera_manager import MultiCameraManager

class TestAdvancedFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stain_clf = StainClassifier()
        cls.symbol_clf = CareSymbolClassifier()
        cls.load_balancer = WorkcellLoadBalancer()
        cls.sustainability = SustainabilityEngine()
        cls.multi_cam = MultiCameraManager()

    def test_stain_classifier_blood_prescription(self):
        # Blood spot
        crop = np.zeros((32, 32, 3), dtype=np.uint8)
        crop[:, :] = [110, 15, 20] # Red-brown
        res = self.stain_clf.classify_stain_crop(crop)
        self.assertEqual(res["stain_type"], "BLOOD")
        self.assertLessEqual(res["prescription"]["max_safe_temp_c"], 30)
        self.assertIn("Proteolytic", res["prescription"]["chemical_agent"])

    def test_stain_classifier_oil_grease(self):
        crop = np.zeros((32, 32, 3), dtype=np.uint8)
        crop[:, :] = [70, 70, 72] # Translucent gray
        res = self.stain_clf.classify_stain_crop(crop)
        self.assertEqual(res["stain_type"], "OIL_GREASE")
        self.assertIn("Solvent", res["prescription"]["chemical_agent"])

    def test_care_symbol_detection(self):
        tag_frame = self.multi_cam.capture_macro_tag_frame()
        res = self.symbol_clf.classify_tag_symbols(tag_frame)
        self.assertGreaterEqual(res["total_symbols_detected"], 1)

    def test_load_balancer_routing_and_dispatch_alert(self):
        self.load_balancer.reset_all_bins()
        # Add multiple denim jeans (~650g each) to BIN_A until washer threshold is reached
        for i in range(25):
            status = self.load_balancer.route_item_to_bin("BIN_A", "Denim", f"Jeans #{i}")

        self.assertGreaterEqual(status["total_weight_kg"], 15.0)
        self.assertIn("READY_FOR_WASHER", status["status"])
        self.assertIsNotNone(status["dispatch_notification"])

        # Unload
        unl = self.load_balancer.unload_bin_to_washer("BIN_A")
        self.assertEqual(unl["status"], "success")
        self.assertEqual(self.load_balancer.bins["BIN_A"]["item_count"], 0)

    def test_sustainability_metrics_tracking(self):
        initial = self.sustainability.get_summary()
        # Record cold wash sorting event
        self.sustainability.record_sorting_event(
            color="DARK",
            fabric="Cotton",
            stains_count=1,
            routed_bin="BIN_C",
            garment_weight_kg=0.5
        )
        updated = self.sustainability.get_summary()
        self.assertGreater(updated["energy_saved_kwh"], initial["energy_saved_kwh"])
        self.assertGreater(updated["total_garments_sorted"], initial["total_garments_sorted"])

    def test_input_validator_rejects_empty_and_invalid_bytes(self):
        # Empty
        valid, _, err = SecurityValidator.validate_and_sanitize_image(b"")
        self.assertFalse(valid)
        self.assertIn("empty", err.lower())

        # Bad signature
        valid, _, err = SecurityValidator.validate_and_sanitize_image(b"NOT_AN_IMAGE_PAYLOAD")
        self.assertFalse(valid)
        self.assertIn("Security Violation", err)

    def test_input_validator_accepts_valid_jpeg(self):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        buf = io.BytesIO()
        Image.fromarray(img).save(buf, format="JPEG")
        valid, san, _ = SecurityValidator.validate_and_sanitize_image(buf.getvalue())
        self.assertTrue(valid)
        self.assertEqual(san.shape, (100, 100, 3))

    def test_safety_guardrails_catches_bleach_on_silk(self):
        decision = {"bin_id": "BIN_A", "recipe": {"temp": "30°C", "bleach_allowed": True}}
        is_safe, violations = SafetyGuardrails.validate_wash_decision(
            decision=decision,
            fabric="Silk",
            color_category="LIGHT",
            stains=[]
        )
        self.assertFalse(is_safe)
        self.assertTrue(any("GUARD_02" in v for v in violations))

    def test_safety_guardrails_catches_hot_wash_on_blood(self):
        decision = {"bin_id": "BIN_B", "recipe": {"temp": "60°C Hot", "bleach_allowed": False}}
        is_safe, violations = SafetyGuardrails.validate_wash_decision(
            decision=decision,
            fabric="Cotton",
            color_category="LIGHT",
            stains=[{"stain_type": "BLOOD"}]
        )
        self.assertFalse(is_safe)
        self.assertTrue(any("GUARD_04" in v for v in violations))

if __name__ == "__main__":
    unittest.main()
