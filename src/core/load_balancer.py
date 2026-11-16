"""
Industrial Bin Capacity Manager & Load Balancing Dispatcher.
Tracks real-time physical weight, garment counts, and volumetric capacity
across Sorting Bins A through G. Automatically signals washing machine dispatch
when optimal industrial load thresholds (e.g. 15 kg) are attained.
"""

from typing import Dict, Any, List

class WorkcellLoadBalancer:
    # Typical Garment Unit Weight Estimates (kg) by Fabric Type
    FABRIC_UNIT_WEIGHTS = {
        "Denim": 0.650,       # Heavy jeans / jackets
        "Wool": 0.500,        # Sweaters / blankets
        "Cotton": 0.220,      # T-shirts / dress shirts
        "Cotton / Blend": 0.240,
        "Polyester": 0.180,   # Activewear / synthetics
        "Silk": 0.150,        # Blouses / scarves
        "Lace": 0.090,        # Delicates
        "Unknown": 0.250
    }

    # Industrial Sorting Bins Specification: Target Load for Washer (kg)
    DEFAULT_BIN_CONFIG = {
        "BIN_A": {"name": "White Cottons - Standard", "max_capacity_kg": 20.0, "target_washer_kg": 15.0},
        "BIN_B": {"name": "White Cottons - Heavy Stain", "max_capacity_kg": 15.0, "target_washer_kg": 10.0},
        "BIN_C": {"name": "Colored/Dark - Cold Wash", "max_capacity_kg": 25.0, "target_washer_kg": 18.0},
        "BIN_D": {"name": "Colored/Dark - Heavy Stain", "max_capacity_kg": 15.0, "target_washer_kg": 10.0},
        "BIN_E": {"name": "Delicates (Silk/Wool)", "max_capacity_kg": 10.0, "target_washer_kg": 6.0},
        "BIN_F": {"name": "Quarantine / VOC / Ozone", "max_capacity_kg": 10.0, "target_washer_kg": 5.0},
        "BIN_G": {"name": "Manual Inspection Station", "max_capacity_kg": 10.0, "target_washer_kg": 5.0}
    }

    def __init__(self):
        self.bins: Dict[str, Dict[str, Any]] = {}
        self.reset_all_bins()

    def reset_all_bins(self):
        """Initializes empty bin telemetry."""
        for bid, cfg in self.DEFAULT_BIN_CONFIG.items():
            self.bins[bid] = {
                "bin_id": bid,
                "name": cfg["name"],
                "max_capacity_kg": cfg["max_capacity_kg"],
                "target_washer_kg": cfg["target_washer_kg"],
                "current_weight_kg": 0.0,
                "item_count": 0,
                "items": [],
                "status": "ACCEPTING"  # ACCEPTING, NEAR_CAPACITY, READY_FOR_WASHER, OVERFLOW_ALERT
            }

    def estimate_garment_weight(self, fabric: str, bbox: List[int] = None) -> float:
        """Estimates garment mass in kilograms based on fabric profile and bbox surface area."""
        base_kg = self.FABRIC_UNIT_WEIGHTS.get(fabric, 0.220)
        if bbox and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            area_px = (x2 - x1) * (y2 - y1)
            # Standard reference frame 1280x720: normal shirt is approx 300,000 px
            scale = max(0.6, min(1.8, area_px / 300000.0))
            return round(base_kg * scale, 3)
        return round(base_kg, 3)

    def route_item_to_bin(self, bin_id: str, fabric: str, item_desc: str, bbox: List[int] = None) -> Dict[str, Any]:
        """
        Updates bin weight and count, returning dispatch and load status.
        """
        if bin_id not in self.bins:
            bin_id = "BIN_G"

        b = self.bins[bin_id]
        item_weight = self.estimate_garment_weight(fabric, bbox)

        b["current_weight_kg"] = round(b["current_weight_kg"] + item_weight, 2)
        b["item_count"] += 1
        b["items"].append({"desc": item_desc, "fabric": fabric, "weight_kg": item_weight})

        # Update bin state
        fill_pct = (b["current_weight_kg"] / b["max_capacity_kg"]) * 100.0
        washer_ready = b["current_weight_kg"] >= b["target_washer_kg"]

        if fill_pct >= 95.0:
            b["status"] = "OVERFLOW_ALERT"
        elif washer_ready:
            b["status"] = "READY_FOR_WASHER"
        elif fill_pct >= 75.0:
            b["status"] = "NEAR_CAPACITY"
        else:
            b["status"] = "ACCEPTING"

        return {
            "bin_id": bin_id,
            "added_weight_kg": item_weight,
            "total_weight_kg": b["current_weight_kg"],
            "item_count": b["item_count"],
            "fill_percentage": round(fill_pct, 1),
            "status": b["status"],
            "dispatch_notification": f"🚨 {bin_id} reached {b['current_weight_kg']} kg! Ready for Industrial Washer." if washer_ready else None
        }

    def unload_bin_to_washer(self, bin_id: str) -> Dict[str, Any]:
        """Simulates unloading the bin into a washing machine drum."""
        if bin_id in self.bins:
            b = self.bins[bin_id]
            unloaded_weight = b["current_weight_kg"]
            unloaded_count = b["item_count"]
            b["current_weight_kg"] = 0.0
            b["item_count"] = 0
            b["items"] = []
            b["status"] = "ACCEPTING"
            return {
                "status": "success",
                "bin_id": bin_id,
                "unloaded_weight_kg": unloaded_weight,
                "unloaded_items": unloaded_count,
                "message": f"Bin {bin_id} cleared and dispatched to wash cycle."
            }
        return {"status": "error", "message": "Invalid Bin ID"}

    def get_workcell_capacity_summary(self) -> Dict[str, Any]:
        """Provides high-level facility dashboard telemetry across all 7 bins."""
        total_weight = sum(b["current_weight_kg"] for b in self.bins.values())
        total_items = sum(b["item_count"] for b in self.bins.values())
        ready_bins = [bid for bid, b in self.bins.items() if b["status"] == "READY_FOR_WASHER"]

        return {
            "total_facility_garments": total_items,
            "total_facility_weight_kg": round(total_weight, 2),
            "bins_ready_for_washing": ready_bins,
            "bins": self.bins
        }
