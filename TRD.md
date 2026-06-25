# Technical Requirements Document (TRD)

## 1. System Architecture
The system follows a microservices-inspired concurrent architecture:
- **Frontend:** Streamlit (Python-based UI) utilizing custom CSS for premium aesthetics.
- **Backend API:** FastAPI (or standard ASGI) handling concurrent requests.
- **AI Core:** PyTorch for executing YOLOv8 and CNN inferences.
- **Hardware Layer:** Robot Operating System (ROS) for mechanical control (future phase).

## 2. AI Pipeline Specifications
### 2.1 Stain Detection (Spatial)
- **Model:** YOLOv8 (nano or small variants for speed).
- **Framework:** Ultralytics.
- **Input:** 640x640 RGB image.
- **Output:** Bounding boxes `[x_center, y_center, width, height]`, confidence score, and class ID (e.g., Oil, Wine).

### 2.2 Fabric Classification (Texture)
- **Model:** MobileNetV3 (optimized for edge inference).
- **Framework:** PyTorch/Torchvision.
- **Input:** 224x224 RGB image crop.
- **Output:** Probability distribution across fabric classes (Cotton, Silk, Wool, etc.).

### 2.3 Color Categorization
- **Model:** ResNet18 or custom lightweight CNN.
- **Input:** 224x224 RGB image.
- **Output:** Base color class.

## 3. The Decision Engine
Implemented in `src/core/decision_engine.py`.
**Logic Flow:**
1. Default sorting is determined by Color (e.g., Whites vs Darks).
2. *Override 1:* If Fabric = "Silk" or "Wool", override to "Delicates Bin".
3. *Override 2:* If Stains detected > 0, override to "Heavy Wash Bin".
4. *Override 3 (Hardware):* If UV Sensor = True OR Odor Sensor = True, override all visual logic and route to "Biohazard/Specialized Cleaning Bin".

## 4. Performance Requirements
- **Latency:** Total software inference time (Vision + Decision Engine) must be under 300ms to maintain conveyor belt throughput.
- **Concurrency:** Models must run on separate threads or asynchronous loops to prevent GIL (Global Interpreter Lock) blocking.
- **Deployment:** The inference server should be containerized using Docker and deployed on an edge computing device (e.g., NVIDIA Jetson Orin) attached directly to the sorting machine.
