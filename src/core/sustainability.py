"""
Sustainability & Chemical ROI Analytics Engine.
Calculates environmental resource savings (Water, Electricity, Carbon Footprint)
and financial return-on-investment (ROI) from automated precision sorting.
"""

from typing import Dict, Any

class SustainabilityEngine:
    # Industrial Standard Benchmarks
    WATER_PER_KG_STANDARD_WASH_L = 12.0      # Liters per kg in commercial washer
    ENERGY_HOT_60C_KWH_PER_KG = 0.65         # kWh per kg for 60C hot wash
    ENERGY_COLD_30C_KWH_PER_KG = 0.20        # kWh per kg for 30C cold wash
    CARBON_FACTOR_KG_PER_KWH = 0.42          # Grid carbon intensity (kg CO2e / kWh)
    AVERAGE_GARMENT_REPLACEMENT_USD = 35.00  # Average commercial replacement cost

    def __init__(self):
        self.total_garments_processed: int = 0
        self.water_saved_liters: float = 0.0
        self.energy_saved_kwh: float = 0.0
        self.carbon_offset_kg: float = 0.0
        self.chemicals_saved_grams: float = 0.0
        self.garments_saved_from_damage: int = 0
        self.financial_savings_usd: float = 0.0

    def record_sorting_event(self,
                             color: str,
                             fabric: str,
                             stains_count: int,
                             routed_bin: str,
                             garment_weight_kg: float = 0.250) -> Dict[str, Any]:
        """
        Updates live sustainability metrics for each sorted garment.
        """
        self.total_garments_processed += 1

        # 1. Energy Savings: Cold wash optimization (BIN_C, BIN_E) vs unnecessary 60C hot wash
        if routed_bin in ["BIN_C", "BIN_E"]:
            kwh_delta = (self.ENERGY_HOT_60C_KWH_PER_KG - self.ENERGY_COLD_30C_KWH_PER_KG) * garment_weight_kg
            self.energy_saved_kwh += kwh_delta
            self.carbon_offset_kg += kwh_delta * self.CARBON_FACTOR_KG_PER_KWH

        # 2. Water Savings: Preventing re-washes via targeted stain pre-treat (BIN_B, BIN_D)
        # In un-sorted laundries, ~14% of stained garments fail to clean and require a full re-wash cycle
        if stains_count > 0 and routed_bin in ["BIN_B", "BIN_D"]:
            water_delta = garment_weight_kg * self.WATER_PER_KG_STANDARD_WASH_L * 1.5
            self.water_saved_liters += water_delta
            # Chemical savings: targeted pre-treat avoids wasting 40g of detergent in a re-wash
            self.chemicals_saved_grams += 25.0

        # 3. Garment Damage Prevention: Delicate Silk/Wool diverted to gentle cycle (BIN_E)
        # or dark bleeders kept away from whites
        if fabric in ["Silk", "Wool"] and routed_bin == "BIN_E":
            self.garments_saved_from_damage += 1
            self.financial_savings_usd += self.AVERAGE_GARMENT_REPLACEMENT_USD

        return self.get_summary()

    def record_bleed_hazard_prevented(self, count: int = 2):
        """Called when a color-bleed hazard is intercepted and separated."""
        self.garments_saved_from_damage += count
        self.financial_savings_usd += count * self.AVERAGE_GARMENT_REPLACEMENT_USD
        # Saving an entire ruined batch also saves the water of an attempted corrective wash
        self.water_saved_liters += count * 15.0

    def get_summary(self) -> Dict[str, Any]:
        """Returns comprehensive facility sustainability metrics."""
        return {
            "total_garments_sorted": self.total_garments_processed,
            "water_saved_liters": round(self.water_saved_liters, 1),
            "energy_saved_kwh": round(self.energy_saved_kwh, 2),
            "carbon_offset_kg_co2": round(self.carbon_offset_kg, 2),
            "chemicals_saved_grams": round(self.chemicals_saved_grams, 1),
            "garments_protected_from_damage": self.garments_saved_from_damage,
            "financial_capital_saved_usd": round(self.financial_savings_usd, 2)
        }
