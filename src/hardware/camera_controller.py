"""
Hardware Camera Controller for Industrial Laundry Sorting Station.
Supports physical USB/GigE/RTSP industrial cameras, with graceful fallback
to synthetic conveyor inspection video feed when physical hardware is detached.
"""

import cv2
import numpy as np
import time
import threading
from typing import Optional, Tuple, Dict, Any

class HardwareCameraController:
    def __init__(self, device_index: int = 0, rtsp_url: Optional[str] = None, width: int = 1280, height: int = 720):
        self.device_index = device_index
        self.rtsp_url = rtsp_url
        self.target_width = width
        self.target_height = height
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_connected = False
        self.is_running = False
        self.lock = threading.Lock()
        
        self.latest_frame: Optional[np.ndarray] = None
        self.latest_timestamp: float = 0.0
        self.uv_mode: bool = False
        self.exposure_val: int = -5
        
        # Diagnostics
        self.fps_counter = 0
        self.current_fps = 0.0
        self._fps_time = time.time()
        
        # Start capture thread
        self._init_camera()
        self._start_capture_loop()

    def _init_camera(self):
        source = self.rtsp_url if self.rtsp_url else self.device_index
        try:
            self.cap = cv2.VideoCapture(source)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                # Verify read
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.is_connected = True
                    self.latest_frame = frame
                    print(f"[HardwareCamera] Connected to physical camera source: {source}")
                    return
        except Exception as e:
            print(f"[HardwareCamera] Failed to connect to camera {source}: {e}")
            
        self.is_connected = False
        print(f"[HardwareCamera] Running in SYNTHETIC CONVEYOR WORKCELL mode.")

    def _start_capture_loop(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.thread.start()

    def _capture_worker(self):
        phase = 0.0
        while self.is_running:
            frame = None
            if self.is_connected and self.cap and self.cap.isOpened():
                ret, grabbed = self.cap.read()
                if ret and grabbed is not None:
                    frame = grabbed
                else:
                    self.is_connected = False
            
            # Generate synthetic conveyor test pattern if camera not connected
            if frame is None:
                frame = self._generate_synthetic_conveyor_frame(phase)
                phase = (phase + 0.03) % (2 * np.pi)
                time.sleep(0.033) # ~30 FPS

            # Apply UV multispectral strobe effect if active
            if self.uv_mode:
                frame = self._apply_uv_filter(frame)

            with self.lock:
                self.latest_frame = frame
                self.latest_timestamp = time.time()
                self.fps_counter += 1
                
                # Update FPS every second
                now = time.time()
                if now - self._fps_time >= 1.0:
                    self.current_fps = self.fps_counter / (now - self._fps_time)
                    self.fps_counter = 0
                    self._fps_time = now

    def _generate_synthetic_conveyor_frame(self, phase: float) -> np.ndarray:
        """
        Renders a simulated high-resolution industrial conveyor inspection zone
        with moving belt markings, lighting glare, and calibrated fiducial markers.
        """
        w, h = self.target_width, self.target_height
        frame = np.full((h, w, 3), 28, dtype=np.uint8) # Dark industrial conveyor base

        # Draw conveyor belt texture with moving lines
        belt_left = int(w * 0.15)
        belt_right = int(w * 0.85)
        cv2.rectangle(frame, (belt_left, 0), (belt_right, h), (40, 42, 45), -1)

        # Conveyor guides / rails
        cv2.rectangle(frame, (belt_left - 15, 0), (belt_left, h), (90, 92, 95), -1)
        cv2.rectangle(frame, (belt_right, 0), (belt_right + 15, h), (90, 92, 95), -1)

        # Moving belt slots
        offset = int((phase / (2 * np.pi)) * 120)
        for y in range(offset - 120, h + 120, 120):
            if 0 <= y < h:
                cv2.line(frame, (belt_left, y), (belt_right, y), (55, 57, 60), 2)

        # Calibrated inspection zone crosshairs and bounding box
        zone_x1, zone_y1 = int(w * 0.25), int(h * 0.15)
        zone_x2, zone_y2 = int(w * 0.75), int(h * 0.85)
        cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 160, 255), 1, cv2.LINE_AA)
        
        # Center target
        cx, cy = w // 2, h // 2
        cv2.drawMarker(frame, (cx, cy), (0, 200, 255), cv2.MARKER_CROSS, 40, 1)

        # Overlay Telemetry Text
        cv2.putText(frame, "WORKCELL CAMERA 01 [STATION 4 - OVERHEAD]", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 225), 1, cv2.LINE_AA)
        status_txt = "LIVE HARDWARE" if self.is_connected else "SYNTHETIC SIMULATOR"
        cv2.putText(frame, f"STATUS: {status_txt} | 1080p | 30.0 FPS", (20, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 120) if self.is_connected else (240, 160, 40), 1)

        # Timestamp
        t_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.latest_timestamp))
        cv2.putText(frame, f"TIME: {t_str}", (w - 280, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        return frame

    def _apply_uv_filter(self, frame: np.ndarray) -> np.ndarray:
        """Simulates 365nm UV Wood's Lamp illumination for biological/chemical fluorescence."""
        uv_frame = frame.copy().astype(np.float32)
        # Suppress Red and Green, amplify Deep Blue/Violet
        uv_frame[:, :, 2] *= 0.35  # Red channel
        uv_frame[:, :, 1] *= 0.50  # Green channel
        uv_frame[:, :, 0] = np.clip(uv_frame[:, :, 0] * 1.6 + 40, 0, 255) # Blue channel
        return np.clip(uv_frame, 0, 255).astype(np.uint8)

    def get_frame(self) -> np.ndarray:
        """Returns the latest captured frame (BGR numpy array)."""
        with self.lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
            return np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)

    def capture_snapshot(self) -> np.ndarray:
        """Triggers a high-quality capture snapshot for AI inference."""
        return self.get_frame()

    def set_uv_mode(self, enabled: bool):
        self.uv_mode = enabled

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "is_connected": self.is_connected,
            "device_source": self.rtsp_url if self.rtsp_url else f"Device #{self.device_index}",
            "resolution": f"{self.target_width}x{self.target_height}",
            "fps": round(self.current_fps, 1),
            "uv_strobe_active": self.uv_mode,
            "last_capture_time": self.latest_timestamp
        }

    def generate_mjpeg_stream(self):
        """Yields MJPEG stream chunks for browser streaming."""
        while self.is_running:
            frame = self.get_frame()
            ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.04)

    def shutdown(self):
        self.is_running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
