"""
Robotic Arm Motion Planner & Pick-and-Place Dispatcher for Industrial Laundry Sorting.
Transforms vision detections into 3D robot workspace coordinates and controls
the pick-and-place execution sequence into Sorting Bins A through G.
"""

import time
import math
import threading
from typing import Dict, Any, List, Optional, Tuple

class RoboticArmController:
    # Physical 3D Target Coordinates for Sorting Bins in Robot Workspace (mm)
    BIN_COORDINATES = {
        "BIN_A": {"x": 380, "y": -360, "z": 120, "name": "White Cottons - Standard Wash"},
        "BIN_B": {"x": 380, "y": -120, "z": 120, "name": "White Cottons - Enzyme Pre-Treat"},
        "BIN_C": {"x": 380, "y": 120, "z": 120, "name": "Colored/Dark - Cold Wash"},
        "BIN_D": {"x": 380, "y": 360, "z": 120, "name": "Colored/Dark - Heavy Stain Pre-Treat"},
        "BIN_E": {"x": 580, "y": -220, "z": 120, "name": "Delicates (Silk/Wool) - Gentle Cycle"},
        "BIN_F": {"x": 580, "y": 0, "z": 120, "name": "Quarantine / VOC Hazard / UV Stained"},
        "BIN_G": {"x": 580, "y": 220, "z": 120, "name": "Manual Inspection Station"}
    }

    HOME_POSITION = {"x": 200, "y": 0, "z": 320, "yaw": 0.0}

    def __init__(self, camera_width: int = 1280, camera_height: int = 720):
        self.cam_w = camera_width
        self.cam_h = camera_height

        # Workspace Calibration parameters (mm per pixel at conveyor height)
        self.scale_x = 0.55  # mm per pixel
        self.scale_y = 0.55  # mm per pixel
        self.conveyor_z = 25 # mm (height of garment top on belt)
        self.conveyor_center_robot_x = 320 # mm
        self.conveyor_center_robot_y = 0   # mm

        # Arm State
        self.current_state = "IDLE"  # IDLE, PLANNING, MOVING_TO_PICK, GRIPPING, TRANSFERRING, RELEASING, RETURNING_HOME, E_STOP
        self.current_pos = dict(self.HOME_POSITION)
        self.is_gripper_engaged = False
        self.emergency_stop = False
        self.lock = threading.Lock()

        # Telemetry & Statistics
        self.cycle_count = 0
        self.bin_counts = {b: 0 for b in self.BIN_COORDINATES}
        self.last_cycle_time_ms = 0
        self.execution_log: List[Dict[str, Any]] = []

    def pixel_to_robot_coords(self, u: float, v: float) -> Tuple[float, float, float]:
        """
        Transforms 2D camera pixel coordinates (u, v) into 3D robot workspace coordinates (X, Y, Z in mm).
        """
        center_u = self.cam_w / 2.0
        center_v = self.cam_h / 2.0

        # Compute displacement from camera center
        dx_pixels = u - center_u
        dy_pixels = v - center_v

        # Convert to robot frame
        # Camera X corresponds to Robot Y, Camera Y corresponds to Robot X along conveyor direction
        robot_x = self.conveyor_center_robot_x + (dy_pixels * self.scale_y)
        robot_y = self.conveyor_center_robot_y + (dx_pixels * self.scale_x)
        robot_z = self.conveyor_z

        return round(robot_x, 1), round(robot_y, 1), round(robot_z, 1)

    def compute_grasp_parameters(self, bbox: List[float], fabric: str = "Cotton") -> Dict[str, Any]:
        """
        Calculates optimal suction grasp centroid, approach angle, and vacuum pressure.
        """
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        width = x2 - x1
        height = y2 - y1

        # Gripper orientation yaw (degrees)
        yaw = 0.0 if width >= height else 90.0

        # Gripper force (Newtons) or vacuum level (kPa)
        if fabric in ["Silk", "Wool", "Lace"]:
            grip_force_n = 4.5 # Soft gentle grip
            approach_speed_pct = 40
        elif fabric in ["Denim", "Canvas"]:
            grip_force_n = 22.0 # High grip
            approach_speed_pct = 90
        else:
            grip_force_n = 12.0 # Standard cotton
            approach_speed_pct = 75

        rx, ry, rz = self.pixel_to_robot_coords(cx, cy)

        return {
            "centroid_pixel": [round(cx, 1), round(cy, 1)],
            "pick_coords_mm": {"x": rx, "y": ry, "z": rz, "yaw": yaw},
            "grip_force_n": grip_force_n,
            "approach_speed_pct": approach_speed_pct,
            "surface_area_px": round(width * height, 1)
        }

    def dispatch_pick_and_place(self,
                                bbox: List[float],
                                bin_id: str,
                                fabric: str = "Cotton",
                                item_label: str = "Garment") -> Dict[str, Any]:
        """
        Executes a simulated or hardware-bridged pick-and-place operation.
        Dispatches trajectory to the target sorting bin and logs cycle telemetry.
        """
        if self.emergency_stop:
            return {
                "status": "aborted",
                "reason": "EMERGENCY_STOP_ACTIVE",
                "message": "Robotic arm is in E-Stop state. Reset safety latch before proceeding."
            }

        start_time = time.time()
        grasp_params = self.compute_grasp_parameters(bbox, fabric)
        target_bin = self.BIN_COORDINATES.get(bin_id, self.BIN_COORDINATES["BIN_G"])

        with self.lock:
            # 1. Planning Trajectory
            self.current_state = "PLANNING"
            time.sleep(0.04)

            # 2. Move to Pick Coordinates
            self.current_state = "MOVING_TO_PICK"
            self.current_pos = grasp_params["pick_coords_mm"]
            time.sleep(0.06)

            # 3. Engage Gripper
            self.current_state = "GRIPPING"
            self.is_gripper_engaged = True
            time.sleep(0.04)

            # 4. Transfer to Target Bin
            self.current_state = "TRANSFERRING"
            self.current_pos = {
                "x": target_bin["x"],
                "y": target_bin["y"],
                "z": target_bin["z"] + 80, # Hover above bin
                "yaw": 0.0
            }
            time.sleep(0.08)

            # 5. Release into Bin
            self.current_state = "RELEASING"
            self.is_gripper_engaged = False
            self.bin_counts[bin_id] = self.bin_counts.get(bin_id, 0) + 1
            self.cycle_count += 1
            time.sleep(0.04)

            # 6. Return Home
            self.current_state = "RETURNING_HOME"
            self.current_pos = dict(self.HOME_POSITION)
            self.current_state = "IDLE"

        cycle_duration_ms = int((time.time() - start_time) * 1000)
        self.last_cycle_time_ms = cycle_duration_ms

        # Generate ROS / G-Code Telemetry Packet
        trajectory_packet = {
            "timestamp": time.time(),
            "cycle_id": f"CYCLE-{self.cycle_count:05d}",
            "arm_state": self.current_state,
            "pick_coords": grasp_params["pick_coords_mm"],
            "target_bin": {
                "id": bin_id,
                "name": target_bin["name"],
                "drop_coords": {"x": target_bin["x"], "y": target_bin["y"], "z": target_bin["z"]}
            },
            "grasp_spec": {
                "force_n": grasp_params["grip_force_n"],
                "speed_pct": grasp_params["approach_speed_pct"]
            },
            "ros_action": "nex_robot_msgs/PickAndPlaceActionGoal",
            "cycle_duration_ms": cycle_duration_ms,
            "item_label": item_label
        }

        self.execution_log.append(trajectory_packet)
        if len(self.execution_log) > 100:
            self.execution_log.pop(0)

        return trajectory_packet

    def trigger_emergency_stop(self, stop: bool = True):
        with self.lock:
            self.emergency_stop = stop
            self.current_state = "E_STOP" if stop else "IDLE"
            if stop:
                self.is_gripper_engaged = False

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "arm_state": self.current_state,
                "emergency_stop": self.emergency_stop,
                "current_position": self.current_pos,
                "gripper_engaged": self.is_gripper_engaged,
                "total_cycles_completed": self.cycle_count,
                "last_cycle_ms": self.last_cycle_time_ms,
                "bin_distribution": dict(self.bin_counts),
                "recent_executions": self.execution_log[-5:]
            }
