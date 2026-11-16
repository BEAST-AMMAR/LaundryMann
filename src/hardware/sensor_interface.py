"""
Hardware Sensor Interface for Industrial Laundry Workcell.
Handles E-Nose VOC gas sensing, UV multispectral fluorescence telemetry,
conveyor belt speed synchronization, and safety interlocks.
"""

import time
import random
import threading
from typing import Dict, Any

class HardwareSensorInterface:
    def __init__(self):
        self.voc_ppm: float = 12.4
        self.uv_fluorescence_idx: float = 3.2
        self.conveyor_speed_mps: float = 0.25  # 25 cm/s
        self.conveyor_running: bool = True
        self.safety_curtain_tripped: bool = False
        
        # Thresholds
        self.VOC_HAZARD_THRESHOLD = 85.0       # PPM: triggers Biohazard/VOC quarantine
        self.UV_STAIN_THRESHOLD = 25.0         # Index: triggers UV invisible stain handling
        
        self.lock = threading.Lock()
        self._running = True
        self._telemetry_thread = threading.Thread(target=self._simulate_drift, daemon=True)
        self._telemetry_thread.start()

    def _simulate_drift(self):
        """Generates realistic industrial ambient sensor fluctuations."""
        while self._running:
            with self.lock:
                # Slight ambient noise
                noise_voc = random.uniform(-0.8, 0.8)
                self.voc_ppm = max(5.0, min(250.0, self.voc_ppm + noise_voc))
                
                noise_uv = random.uniform(-0.3, 0.3)
                self.uv_fluorescence_idx = max(0.0, min(100.0, self.uv_fluorescence_idx + noise_uv))
            time.sleep(1.0)

    def set_sensor_overrides(self, voc_ppm: float, uv_index: float):
        """Allows direct hardware injection or test override."""
        with self.lock:
            self.voc_ppm = float(voc_ppm)
            self.uv_fluorescence_idx = float(uv_index)

    def trigger_voc_spike(self, ppm: float = 120.0):
        with self.lock:
            self.voc_ppm = ppm

    def trigger_uv_fluorescence(self, idx: float = 65.0):
        with self.lock:
            self.uv_fluorescence_idx = idx

    def reset_ambient(self):
        with self.lock:
            self.voc_ppm = 14.5
            self.uv_fluorescence_idx = 4.0

    def set_conveyor_speed(self, speed_mps: float):
        with self.lock:
            self.conveyor_speed_mps = max(0.0, min(1.0, speed_mps))
            self.conveyor_running = self.conveyor_speed_mps > 0

    def get_telemetry(self) -> Dict[str, Any]:
        with self.lock:
            is_voc_hazard = self.voc_ppm >= self.VOC_HAZARD_THRESHOLD
            is_uv_stain = self.uv_fluorescence_idx >= self.UV_STAIN_THRESHOLD
            
            return {
                "timestamp": time.time(),
                "voc_e_nose": {
                    "ppm": round(self.voc_ppm, 1),
                    "hazard_flag": is_voc_hazard,
                    "threshold_ppm": self.VOC_HAZARD_THRESHOLD,
                    "status": "DANGER - QUARANTINE" if is_voc_hazard else "NORMAL AMBIENT"
                },
                "uv_multispectral": {
                    "fluorescence_idx": round(self.uv_fluorescence_idx, 1),
                    "invisible_stain_detected": is_uv_stain,
                    "threshold_idx": self.UV_STAIN_THRESHOLD,
                    "status": "FLUORESCENCE DETECTED" if is_uv_stain else "CLEAR"
                },
                "conveyor": {
                    "speed_mps": round(self.conveyor_speed_mps, 2),
                    "is_running": self.conveyor_running,
                    "state": "ACTIVE" if self.conveyor_running else "STOPPED"
                },
                "safety": {
                    "curtain_tripped": self.safety_curtain_tripped,
                    "interlocks_engaged": True
                }
            }
