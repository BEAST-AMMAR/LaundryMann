"""
Deterministic Industrial Safety Guardrails & Policy Enforcement.
Applies zero-tolerance validation rules to prevent clothing damage,
chemical bleaching catastrophes, dye bleed contamination, and robotic arm collisions.
"""

from typing import Dict, Any, List, Tuple

class SafetyGuardrailViolation(Exception):
    """Raised when an operation attempts to violate a safety policy."""
    pass

class SafetyGuardrails:
    # Maximum allowable physical robotic grip force (Newtons) to prevent fabric tearing
    MAX_ALLOWABLE_GRIP_FORCE_N = 25.0
    
    # Maximum allowable delicate water temperature (Celsius)
    MAX_DELICATE_TEMP_C = 30.0

    @classmethod
    def validate_wash_decision(cls,
                               decision: Dict[str, Any],
                               fabric: str,
                               color_category: str,
                               stains: List[Dict[str, Any]],
                               ocr_rules: List[str] = None) -> Tuple[bool, List[str]]:
        """
        Validates an AI-generated wash recipe against non-negotiable safety guardrails.
        Returns: (is_safe, list_of_violations)
        """
        violations = []
        rules = ocr_rules or []
        recipe = decision.get("recipe", {})
        temp_str = str(recipe.get("temp", ""))
        bleach_allowed = recipe.get("bleach_allowed", False)

        # GUARD 1: Dry Clean Only Prohibition
        is_dry_clean = any("dry clean" in str(r).lower() for r in rules)
        if is_dry_clean and decision.get("bin_id") != "BIN_G":
            violations.append("GUARD_01_VIOLATION: Garment is Dry Clean Only. Wet washing is prohibited.")

        # GUARD 2: Bleach Prohibition on Delicates & Colored Garments
        is_delicate = fabric in ["Silk", "Wool", "Lace"]
        is_colored = color_category in ["DARK", "COLORED"]
        if bleach_allowed and (is_delicate or is_colored):
            violations.append("GUARD_02_VIOLATION: Bleach permitted on delicate or colored fabric. Risk of irreversible fiber destruction.")

        # GUARD 3: Delicates Temperature Ceiling (Max 30°C)
        if is_delicate:
            if "40" in temp_str or "60" in temp_str or "hot" in temp_str.lower():
                violations.append("GUARD_03_VIOLATION: Temperature exceeds 30°C on delicate fabric. Risk of felting and thermal shrinkage.")

        # GUARD 4: Blood Stain Heat Restriction (Hot water sets blood protein permanently)
        has_blood = any(s.get("stain_type") == "BLOOD" or "blood" in str(s).lower() for s in stains)
        if has_blood:
            if "40" in temp_str or "60" in temp_str or "hot" in temp_str.lower():
                violations.append("GUARD_04_VIOLATION: Hot wash prescribed for blood stain. Blood protein coagulates irreversibly above 35°C.")

        is_safe = len(violations) == 0
        return is_safe, violations

    @classmethod
    def validate_robot_trajectory(cls, grasp_params: Dict[str, Any], e_stop_active: bool) -> Tuple[bool, str]:
        """Validates mechanical robotic pick-and-place parameters before actuation."""
        if e_stop_active:
            return False, "GUARD_05_VIOLATION: Robotic arm cannot execute command while Emergency Stop is engaged."

        grip_force = grasp_params.get("grip_force_n", 12.0)
        if grip_force > cls.MAX_ALLOWABLE_GRIP_FORCE_N:
            return False, f"GUARD_06_VIOLATION: Requested grip force {grip_force} N exceeds maximum allowable safety threshold of {cls.MAX_ALLOWABLE_GRIP_FORCE_N} N."

        return True, "OK"
