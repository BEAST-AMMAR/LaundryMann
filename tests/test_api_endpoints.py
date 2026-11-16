import unittest
from fastapi.testclient import TestClient
import numpy as np
import io
from PIL import Image

from api import app

class TestFastAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_ready_endpoint(self):
        res = self.client.get("/health/ready")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)
        self.assertIn("subsystems", data)

    def test_sensors_endpoint(self):
        res = self.client.get("/hardware/sensors")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("voc_e_nose", data)
        self.assertIn("uv_multispectral", data)
        self.assertIn("conveyor", data)

    def test_robot_status_endpoint(self):
        res = self.client.get("/robot/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("arm_state", data)
        self.assertIn("current_position", data)
        self.assertIn("bin_distribution", data)

    def test_robot_dispatch_endpoint(self):
        res = self.client.post("/robot/dispatch", data={"bin_id": "BIN_C", "fabric": "Cotton"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["dispatch_packet"]["target_bin"]["id"], "BIN_C")

    def test_analyze_with_image_upload(self):
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        img[:, :] = [180, 20, 20] # Red
        pil_img = Image.fromarray(img)
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG")
        buf.seek(0)

        res = self.client.post(
            "/analyze",
            files={"file": ("test_shirt.jpg", buf, "image/jpeg")},
            data={"odor_detected": "false", "uv_fluorescence": "false"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("decision", data)
        self.assertIn("robotics", data)
        self.assertIn("operations", data)
        self.assertIn("bin_load", data["operations"])
        self.assertIn("sustainability", data["operations"])

    def test_camera_capture_endpoint(self):
        res = self.client.get("/hardware/camera/capture")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("image_base64", data)

    def test_macro_tag_camera_endpoint(self):
        res = self.client.get("/hardware/camera/macro_tag")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("image_base64", data)

    def test_load_balancer_status_endpoint(self):
        res = self.client.get("/load_balancer/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("bins", data)
        self.assertIn("total_facility_garments", data)

    def test_sustainability_metrics_endpoint(self):
        res = self.client.get("/sustainability/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("water_saved_liters", data)
        self.assertIn("energy_saved_kwh", data)

    def test_evals_benchmark_endpoint(self):
        res = self.client.get("/evals/benchmark")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("overall_status", data)
        self.assertIn("metrics", data)

if __name__ == "__main__":
    unittest.main()
