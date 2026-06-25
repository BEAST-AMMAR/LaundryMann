class LaundryDecisionEngine:
    """
    The deterministic rule-engine that takes inputs from the multi-stage AI pipeline
    and outputs the physical routing bin and wash parameters.
    """
    
    def __init__(self):
        # Bins available in the robotic factory
        self.BINS = {
            "BIN_A": "White Cottons - Standard Wash",
            "BIN_B": "White Cottons - Heavy Enzyme Pre-Treat (Stained)",
            "BIN_C": "Colored/Dark Cottons - Cold Wash",
            "BIN_D": "Colored/Dark - Heavy Stain Pre-Treat",
            "BIN_E": "Delicates (Silk/Wool) - Gentle Cold Cycle",
            "BIN_F": "Ozone Treatment (Odor Detected) / UV Bleach",
            "BIN_G": "Manual Inspection Required"
        }

    def decide_routing(self, color: str, fabric: str, stains: list, odor_detected: bool = False, uv_fluorescence: bool = False):
        """
        Calculates the routing decision based on AI outputs.
        """
        # 1. Odor / Invisible Stain Override (The Multispectral/E-Nose Check)
        if odor_detected:
            return "BIN_F", self.BINS["BIN_F"]
            
        # If UV camera finds fluorescence but normal YOLO found no stain
        # it means there's an invisible chemical/fluid stain
        has_invisible_stain = uv_fluorescence and len(stains) == 0
        has_visible_stain = len(stains) > 0
        
        is_stained = has_visible_stain or has_invisible_stain

        # 2. Fabric Override
        if fabric in ["Silk", "Wool"]:
            # Delicates require extreme care. If stained, might need manual spot clean.
            if is_stained:
                return "BIN_G", self.BINS["BIN_G"]
            return "BIN_E", self.BINS["BIN_E"]

        # 3. Standard Sorting Logic (Cotton/Polyester)
        if color == "LIGHT":
            if is_stained:
                return "BIN_B", self.BINS["BIN_B"]
            else:
                return "BIN_A", self.BINS["BIN_A"]
        
        elif color in ["DARK", "COLORED"]:
            if is_stained:
                return "BIN_D", self.BINS["BIN_D"]
            else:
                return "BIN_C", self.BINS["BIN_C"]

        # Fallback
        return "BIN_G", self.BINS["BIN_G"]

