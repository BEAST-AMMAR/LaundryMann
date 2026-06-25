# Nexus Laundry AI: Implementation Plan

## Phase 1: Software Architecture Foundation
1. Establish `src/` directory with `models/` and `core/` submodules.
2. Define base abstractions for `StainDetector`, `FabricClassifier`, and `ColorClassifier`.
3. Create the `LaundryDecisionEngine` with a deterministic routing matrix.

## Phase 2: AI Pipeline Implementation
1. Integrate YOLOv8 for spatial stain localization.
2. Integrate MobileNetV3 for texture/fabric analysis.
3. Integrate custom CNN (ResNet-based) for precise color categorization.
4. Establish asynchronous inference via `api.py` using `concurrent.futures`.

## Phase 3: Hardware Logic Integration
1. Define API endpoints to receive telemetry from E-Nose (VOC sensors) and Multispectral cameras (UV/NIR).
2. Implement override rules in the Decision Engine (e.g., if VOC > threshold, route to biohazard bin).

## Phase 4: UI/UX Development
1. Build a Streamlit-based commercial factory dashboard.
2. Implement Glassmorphism aesthetics, dark mode, and real-time telemetry visualization.
3. Simulate hardware sensor toggles for demonstration purposes.

## Phase 5: Real Dataset Acquisition & Model Training
1. Source extensive real-world datasets for stains, fabric types, and colors (e.g., DeepFashion, custom Kaggle stain datasets).
2. Format data into YOLO and ImageNet structures.
3. Train models on cloud GPUs (AWS/GCP) for 100+ epochs.
4. Export weights (`.pt`, `.onnx`) for local deployment.

## Phase 6: Hardware Build & Robotic Integration
1. Assemble the robotic arm (e.g., using ROS - Robot Operating System).
2. Mount the multispectral cameras and VOC sensors over the conveyor belt.
3. Establish a WebSocket connection between the AI inference server and the robotic arm controllers.
4. Conduct physical pick-and-place calibration and latency testing.
