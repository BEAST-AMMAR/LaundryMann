"""
Nexus Laundry AI: Automated Benchmark Evaluation & Safety Guardrail Harness.
Evaluates accuracy, F1-scores, zero-tolerance safety guardrails,
and edge latency metrics across the entire perception and robotics workcell.
"""

import time
import os
import sys
import numpy as np
from typing import Dict, Any, List

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.models.color_classifier import ColorClassifier
from src.models.fabric_classifier import FabricClassifier
from src.models.stain_classifier import StainClassifier
from src.models.care_symbol_classifier import CareSymbolClassifier
from src.core.decision_engine import LaundryDecisionEngine
from src.security.guardrails import SafetyGuardrails
from src.models.edge_optimizer import EdgeOptimizer

class WorkcellBenchmarkHarness:
    def __init__(self):
        self.color_clf = ColorClassifier()
        self.fabric_clf = FabricClassifier()
        self.stain_clf = StainClassifier()
        self.symbol_clf = CareSymbolClassifier()
        self.decision_engine = LaundryDecisionEngine()
        self.optimizer = EdgeOptimizer()

    def run_color_eval(self) -> Dict[str, Any]:
        """Evaluates CIELAB and HSV color classification and bleed risk prediction."""
        test_cases = [
            {"rgb": [250, 250, 250], "expected_cat": "LIGHT", "expected_bleed": "LOW", "name": "White"},
            {"rgb": [20, 20, 25], "expected_cat": "DARK", "expected_bleed": "HIGH", "name": "Black"},
            {"rgb": [130, 15, 20], "expected_cat": "DARK", "expected_bleed": "HIGH", "name": "Dark Red"},
            {"rgb": [20, 35, 100], "expected_cat": "DARK", "expected_bleed": "HIGH", "name": "Navy Blue"},
            {"rgb": [220, 215, 195], "expected_cat": "LIGHT", "expected_bleed": "LOW", "name": "Cream / Beige"},
            {"rgb": [220, 30, 30], "expected_cat": "COLORED", "expected_bleed": "HIGH", "name": "Bright Red"}
        ]

        correct_cat = 0
        correct_bleed = 0

        for tc in test_cases:
            img = np.zeros((80, 80, 3), dtype=np.uint8)
            img[:, :] = tc["rgb"]
            prof = self.color_clf.analyze_color_profile(img)

            if prof["category"] == tc["expected_cat"]:
                correct_cat += 1
            if prof["bleed_risk"] == tc["expected_bleed"]:
                correct_bleed += 1

        total = len(test_cases)
        return {
            "total_cases": total,
            "category_accuracy": round(correct_cat / total, 3),
            "bleed_risk_accuracy": round(correct_bleed / total, 3),
            "passed": (correct_cat == total and correct_bleed == total)
        }

    def run_stain_classification_eval(self) -> Dict[str, Any]:
        """Evaluates multi-class stain discrimination and chemistry prescription."""
        test_stains = [
            {"rgb": [110, 15, 20], "expected": "BLOOD"},       # Dark red-brown
            {"rgb": [120, 10, 70], "expected": "RED_WINE"},     # Magenta/violet
            {"rgb": [70, 70, 72], "expected": "OIL_GREASE"},     # Translucent gray-neutral
            {"rgb": [115, 80, 35], "expected": "COFFEE_TEA"},   # Yellow-brown
            {"rgb": [15, 25, 95], "expected": "INK_DYE"}        # Deep blue
        ]

        correct = 0
        for tc in test_stains:
            crop = np.zeros((32, 32, 3), dtype=np.uint8)
            crop[:, :] = tc["rgb"]
            res = self.stain_clf.classify_stain_crop(crop)
            if res["stain_type"] == tc["expected"]:
                correct += 1

        total = len(test_stains)
        return {
            "total_cases": total,
            "accuracy": round(correct / total, 3),
            "passed": correct >= 4
        }

    def run_safety_guardrails_eval(self) -> Dict[str, Any]:
        """
        Adversarial evaluation testing that safety guardrails catch 100% of illegal/dangerous actions.
        """
        adversarial_tests = [
            # 1. Hot wash on blood
            {
                "decision": {"bin_id": "BIN_B", "recipe": {"temp": "60°C Hot", "bleach_allowed": True}},
                "fabric": "Cotton",
                "color": "LIGHT",
                "stains": [{"stain_type": "BLOOD"}],
                "expected_violation": "GUARD_04_VIOLATION"
            },
            # 2. Bleach on Silk
            {
                "decision": {"bin_id": "BIN_A", "recipe": {"temp": "30°C", "bleach_allowed": True}},
                "fabric": "Silk",
                "color": "LIGHT",
                "stains": [],
                "expected_violation": "GUARD_02_VIOLATION"
            },
            # 3. Wet wash on Dry Clean Only
            {
                "decision": {"bin_id": "BIN_A", "recipe": {"temp": "40°C", "bleach_allowed": False}},
                "fabric": "Cotton",
                "color": "LIGHT",
                "stains": [],
                "ocr_rules": ["Dry Clean Only"],
                "expected_violation": "GUARD_01_VIOLATION"
            },
            # 4. Hot water on Wool
            {
                "decision": {"bin_id": "BIN_E", "recipe": {"temp": "40°C Warm", "bleach_allowed": False}},
                "fabric": "Wool",
                "color": "LIGHT",
                "stains": [],
                "expected_violation": "GUARD_03_VIOLATION"
            }
        ]

        intercepted = 0
        for adv in adversarial_tests:
            is_safe, violations = SafetyGuardrails.validate_wash_decision(
                decision=adv["decision"],
                fabric=adv["fabric"],
                color_category=adv["color"],
                stains=adv["stains"],
                ocr_rules=adv.get("ocr_rules")
            )
            if not is_safe and any(adv["expected_violation"] in v for v in violations):
                intercepted += 1

        # Test Robotic E-Stop & Grip Force Guard
        e_stop_pass, _ = SafetyGuardrails.validate_robot_trajectory({"grip_force_n": 10.0}, e_stop_active=True)
        force_pass, _ = SafetyGuardrails.validate_robot_trajectory({"grip_force_n": 40.0}, e_stop_active=False)

        if not e_stop_pass and not force_pass:
            intercepted += 2

        total = len(adversarial_tests) + 2
        return {
            "total_adversarial_trials": total,
            "threats_intercepted": intercepted,
            "zero_tolerance_enforced": intercepted == total
        }

    def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """Runs complete benchmark suite across all workcell subsystems."""
        t_start = time.perf_counter()

        color_res = self.run_color_eval()
        stain_res = self.run_stain_classification_eval()
        guard_res = self.run_safety_guardrails_eval()

        # Latency evaluation on sample crop
        dummy_crop = np.full((120, 120, 3), 180, dtype=np.uint8)
        lat_prof = self.optimizer.profile_inference(self.color_clf.analyze_color_profile, dummy_crop, iterations=10)

        total_time_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

        return {
            "timestamp": time.time(),
            "overall_status": "BENCHMARK_PASSED" if (color_res["passed"] and stain_res["passed"] and guard_res["zero_tolerance_enforced"]) else "BENCHMARK_FAILED",
            "execution_duration_ms": total_time_ms,
            "metrics": {
                "color_classification": color_res,
                "stain_classification": stain_res,
                "safety_guardrails": guard_res,
                "latency_profiling": {
                    "p50_ms": lat_prof["p50_ms"],
                    "p95_ms": lat_prof["p95_ms"],
                    "target_sub_30ms_achieved": lat_prof["p95_ms"] < 30.0
                }
            }
        }

if __name__ == "__main__":
    harness = WorkcellBenchmarkHarness()
    results = harness.run_full_benchmark_suite()
    print("Benchmark Results:", results)
