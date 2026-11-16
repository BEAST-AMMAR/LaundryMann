"""
Industrial Laundry Decision Engine for Autonomous Robotic Sorting Workcell.
Determines sorting bin destination, robotic arm trajectory coordinates,
wash cycle recipes, and safety interlocks with explainable audit trails.
"""

from typing import Dict, Any, List, Tuple, Optional

class LaundryDecisionEngine:
    # Factory Workcell Sorting Bins Specification
    BINS = {
        "BIN_A": {
            "name": "White Cottons - Standard Wash",
            "coords": {"x": 380, "y": -360, "z": 120},
            "recipe": {
                "temp": "40°C Warm",
                "cycle": "Normal / Heavy Cotton",
                "detergent": "Standard Powder / Brightener",
                "spin": "High (1200 RPM)",
                "bleach_allowed": True
            }
        },
        "BIN_B": {
            "name": "White Cottons - Heavy Enzyme Pre-Treat (Stained)",
            "coords": {"x": 380, "y": -120, "z": 120},
            "recipe": {
                "temp": "60°C Hot",
                "cycle": "Intensive Stain Cycle with Soak",
                "detergent": "Heavy Bio-Enzyme + Oxygen Booster",
                "spin": "High (1200 RPM)",
                "bleach_allowed": True
            }
        },
        "BIN_C": {
            "name": "Colored/Dark Cottons - Cold Wash (Colorfast)",
            "coords": {"x": 380, "y": 120, "z": 120},
            "recipe": {
                "temp": "20°C - 30°C Cold",
                "cycle": "Color-Safe Normal",
                "detergent": "Color-Protect Liquid Detergent",
                "spin": "Medium (800 RPM)",
                "bleach_allowed": False
            }
        },
        "BIN_D": {
            "name": "Colored/Dark - Heavy Stain Pre-Treat",
            "coords": {"x": 380, "y": 360, "z": 120},
            "recipe": {
                "temp": "30°C Cold (Protects Dyes from Setting)",
                "cycle": "Targeted Enzyme Spot Clean",
                "detergent": "Non-Chlorine Color Stain Remover",
                "spin": "Medium (800 RPM)",
                "bleach_allowed": False
            }
        },
        "BIN_E": {
            "name": "Delicates (Silk/Wool) - Gentle Cold Cycle",
            "coords": {"x": 580, "y": -220, "z": 120},
            "recipe": {
                "temp": "Cold / Tap (Max 30°C)",
                "cycle": "Delicates / Woolens Gentle",
                "detergent": "pH-Neutral Wool/Silk Liquid",
                "spin": "Very Low (400 RPM) / Flat Dry",
                "bleach_allowed": False
            }
        },
        "BIN_F": {
            "name": "Ozone Treatment / VOC Quarantine (Odor or UV Hazard)",
            "coords": {"x": 580, "y": 0, "z": 120},
            "recipe": {
                "temp": "Cold Injection / Ozone Cycle",
                "cycle": "Ozone Gas Sterilization / Deodorization",
                "detergent": "Sanitizing Deodorizer",
                "spin": "Low (600 RPM)",
                "bleach_allowed": False
            }
        },
        "BIN_G": {
            "name": "Manual Inspection Required (High Risk / Delicate Stain)",
            "coords": {"x": 580, "y": 220, "z": 120},
            "recipe": {
                "temp": "Operator Discretion",
                "cycle": "Manual Spot Cleaning Station",
                "detergent": "Specialist Spot Treatment",
                "spin": "No Spin",
                "bleach_allowed": False
            }
        }
    }

    def decide_industrial_routing(self,
                                  color: str,
                                  fabric: str,
                                  stains: list,
                                  odor_detected: bool = False,
                                  uv_fluorescence: bool = False,
                                  ocr_constraints: Optional[List[str]] = None,
                                  color_name: Optional[str] = None,
                                  bleed_risk: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates the exact robotic sorting bin and comprehensive industrial recipe.
        """
        reasons = []
        alerts = []
        ocr_rules = ocr_constraints or []

        # 1. Critical Hard Constraint: Care Label "Dry Clean Only"
        is_dry_clean = any("dry clean" in str(rule).lower() for rule in ocr_rules)
        if is_dry_clean:
            bin_id = "BIN_G"
            reasons.append("Care tag specifies Dry Clean Only: water immersion will damage garment.")
            alerts.append("CRITICAL: Do not wash. Send to Dry Cleaning.")
            return self._build_decision_packet(bin_id, reasons, alerts, ocr_rules)

        # 2. Hardware Sensor Overrides: E-Nose VOC Odor or UV Invisible Contaminant
        if odor_detected:
            bin_id = "BIN_F"
            reasons.append("Electronic Nose (VOC) triggered: Volatile organic compounds/smoke/chemical detected.")
            alerts.append("HAZARD: Diverted to Ozone Decontamination Bin F.")
            return self._build_decision_packet(bin_id, reasons, alerts, ocr_rules)

        has_visible_stain = len(stains) > 0
        has_uv_stain = uv_fluorescence and not has_visible_stain
        is_stained = has_visible_stain or has_uv_stain

        if has_uv_stain:
            bin_id = "BIN_F"
            reasons.append("UV Multispectral illumination revealed invisible biological/chemical fluid stain.")
            alerts.append("UV FLUORESCENCE: Diverted to Ozone / Bleach Sanitation Bin F.")
            return self._build_decision_packet(bin_id, reasons, alerts, ocr_rules)

        # 3. Delicate Fabric Handling (Silk, Wool, Lace)
        fabric_clean = str(fabric).capitalize()
        if any(delicate in fabric_clean for delicate in ["Silk", "Wool", "Lace", "Cashmere"]):
            if is_stained:
                bin_id = "BIN_G"
                reasons.append(f"Stained delicate ({fabric_clean}): Machine stain treatment could ruin fibers. Requires manual spot clean.")
            else:
                bin_id = "BIN_E"
                reasons.append(f"Delicate fabric ({fabric_clean}): Routed to gentle cold cycle to prevent fiber shrinkage and felting.")
            return self._build_decision_packet(bin_id, reasons, alerts, ocr_rules)

        # 4. Standard Sorting Logic based on Color & Stains
        color_category = str(color).upper()
        if "LIGHT" in color_category or color_name in ["White", "Light Gray", "Beige / Cream"]:
            if is_stained:
                bin_id = "BIN_B"
                reasons.append(f"Stained light garment ({len(stains)} visible stains): Routed to heavy enzyme pre-treat with warm soak.")
            else:
                bin_id = "BIN_A"
                reasons.append("Clean light/white garment: Standard cotton wash.")
        elif "DARK" in color_category or "COLORED" in color_category:
            if is_stained:
                bin_id = "BIN_D"
                reasons.append(f"Stained dark/colored garment: Routed to targeted color-safe stain cycle at 30°C to preserve dyes.")
            else:
                bin_id = "BIN_C"
                reasons.append("Clean dark/colored garment: Cold wash cycle to prevent dye fading and color run.")
        else:
            bin_id = "BIN_G"
            reasons.append("Ambiguous classification: Routed to inspection.")

        # Check for bleach prohibition on care tag
        if any("do not bleach" in str(r).lower() for r in ocr_rules):
            alerts.append("Label Warning: Bleach prohibited on this garment.")

        return self._build_decision_packet(bin_id, reasons, alerts, ocr_rules)

    def _build_decision_packet(self, bin_id: str, reasons: List[str], alerts: List[str], ocr_rules: List[str]) -> Dict[str, Any]:
        bin_meta = self.BINS.get(bin_id, self.BINS["BIN_G"])
        recipe = dict(bin_meta["recipe"])

        # Override recipe if care label dictates colder wash
        for rule in ocr_rules:
            if "cold" in rule.lower() or "30c" in rule.lower():
                recipe["temp"] = "Cold (Max 30°C)"
            if "line dry" in rule.lower():
                recipe["spin"] = "Low Spin (Line Dry Required)"

        return {
            "bin_id": bin_id,
            "bin_name": bin_meta["name"],
            "robot_target_coords": bin_meta["coords"],
            "recipe": recipe,
            "reasons": reasons,
            "alerts": alerts,
            "instructions": f"{bin_meta['name']} | Temp: {recipe['temp']} | Cycle: {recipe['cycle']} | Detergent: {recipe['detergent']}"
        }

    def decide_routing(self,
                       color: str,
                       fabric: str,
                       stains: list,
                       odor_detected: bool = False,
                       uv_fluorescence: bool = False,
                       ocr_instructions: Optional[List[str]] = None) -> Tuple[str, str]:
        """
        Original method interface returning (bin_id, instructions_string).
        Maintains complete backward compatibility across all callers.
        """
        result = self.decide_industrial_routing(
            color=color,
            fabric=fabric,
            stains=stains,
            odor_detected=odor_detected,
            uv_fluorescence=uv_fluorescence,
            ocr_constraints=ocr_instructions
        )
        return result["bin_id"], result["instructions"]
