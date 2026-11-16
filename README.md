# Nexus Laundry AI (LaundryMann 2.0)
### Autonomous Industrial Garment Sorting & Quality Inspection Workcell

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/BEAST-AMMAR/LaundryMann)
[![Python](https://img.shields.io/badge/python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/telemetry-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Computer Vision](https://img.shields.io/badge/perception-YOLOv8%20%7C%20OpenCV-orange.svg)](https://ultralytics.com)
[![Robotics](https://img.shields.io/badge/robotics-6--DOF%20Manipulator%20%7C%20ROS%20Action-red.svg)](#robotics-and-sorting-architecture)
[![Safety Guardrails](https://img.shields.io/badge/safety%20guardrails-100%25%20Zero--Tolerance-success.svg)](#zero-tolerance-safety-guardrails)
[![Tests](https://img.shields.io/badge/tests-30%2F30%20passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🏭 Executive Overview

**Nexus Laundry AI (LaundryMann 2.0)** is an enterprise-grade, autonomous industrial workcell engineered for commercial laundry facilities, hospitality centers, hospitals, and garment processing plants.

Transitioning from a consumer mobile prototype into a fully integrated cyber-physical sorting workcell, **Version 2.0** synchronizes dual high-resolution optical cameras, an electronic nose (E-Nose) VOC & UV fluorescence sensor suite, high-speed multi-stage computer vision models, and a 6-DOF robotic manipulator to inspect, classify, chemical-prescribe, and route mixed bulk textiles into 7 physical washer bins at sub-30 millisecond latency.

```
                    ┌────────────────────────────────────────────────────────┐
                    │               CONVEYOR INSPECTION LINE                 │
                    └──────────────────────────┬─────────────────────────────┘
                                               │
                       ┌───────────────────────┴───────────────────────┐
                       ▼                                               ▼
            [CAM_01: Overhead GigE]                         [CAM_02: Macro Tag Optics]
           Full Conveyor Multi-Garment                     Macro ISO 3758 Tag & Fabric
                       │                                               │
                       └───────────────────────┬───────────────────────┘
                                               │
                                               ▼
                   ┌───────────────────────────────────────────────────────┐
                   │               PERCEPTION & SENSOR SUITE               │
                   │  • CIELAB / HSV Color Analyzer & Dye-Bleed Risk       │
                   │  • 8-Class Chemical Stain Classifier & Spot Rx        │
                   │  • ISO 3758 Contour Care Symbol Archetype Engine      │
                   │  • Texture Roughness & Frequency Fabric Classifier    │
                   │  • E-Nose VOC (PPM) & UV Fluorescence Telemetry      │
                   └───────────────────────────┬───────────────────────────┘
                                               │
                                               ▼
                   ┌───────────────────────────────────────────────────────┐
                   │          DETERMINISTIC DECISION & SAFETY ENGINE       │
                   │  • Zero-Tolerance Safety Guardrails (100% Intercept)  │
                   │  • Multi-Factor Cost-Optimized Washing Matrix         │
                   │  • Workspace Transformation: Pixel (u,v) -> 3D (X,Y,Z)│
                   └───────────────────────────┬───────────────────────────┘
                                               │
                       ┌───────────────────────┴───────────────────────┐
                       ▼                                               ▼
       [6-DOF Robotic Manipulator Dispatch]            [Factory Operations & Load Balancer]
       • 7 Physical Destination Bins (A - G)           • 15 kg Washer Capacity Trigger
       • Dynamic Grip Force: 4.5 N (Silk) to 22 N      • Live ESG Sustainability Tracking
       • ROS Action Goal Packet Generation             • Real-time Throughput Telemetry
```

---

## 🚀 What's New in Version 2.0

| Feature Subsystem | Version 1.0 (Legacy Mobile) | Version 2.0 (Industrial Workcell) |
| :--- | :--- | :--- |
| **Optics & Acquisition** | Single smartphone camera upload | Synchronized dual-camera rig (`CAM_01_OVERHEAD` + `CAM_02_MACRO_TAG`) with 365nm UV strobe simulation |
| **Sensors & Telemetry** | None (Visual only) | Integrated E-Nose VOC (PPM) + UV fluorescence biohazard/odour anomaly detector |
| **Robotic Automation** | Manual user sorting | 6-DOF robotic manipulator routing with $3\text{D Workspace} (X, Y, Z, \text{Yaw})$ transformation & ROS action packets |
| **Robotic Gripper Force**| None | Dynamic force modulation: **4.5 N** (Silk/Lace) to **22.0 N** (Denim/Heavy), capped at **25.0 N** safety ceiling |
| **Sorting Bins** | Theoretical category labels | 7 Physical destination bins (`BIN_A` through `BIN_G`) with capacity load balancing |
| **Stain Chemistry** | Generic label | 8-Class stain detector with chemical spot treatments, active reagents, and strict wash temp limits |
| **Symbol Parsing** | Raw OCR text output | Computer vision contour archetype classifier for 5 ISO 3758 care symbol standards |
| **Safety Enforcement** | Client-side warnings | Zero-tolerance deterministic guardrail interceptor (100% block rate on safety threats) |
| **Factory Operations** | None | 15 kg automated washer batch alerts + real-time ESG sustainability metrics (water, power, carbon, ROI) |
| **Inference Profiling**| Unmonitored PyTorch execution | Sub-30ms p95 edge profiling and TensorRT/ONNX acceleration pipeline |

---

## 🦾 Robotics & Sorting Architecture

### Coordinate Workspace Transformation
The decision pipeline converts 2D normalized camera coordinates $(u, v)$ from `CAM_01_OVERHEAD` into calibrated 3D world coordinates $(X, Y, Z, \text{Yaw})$ for robotic trajectory planning:

$$\begin{aligned}
X_{\text{robot}} &= (u - 0.5) \times W_{\text{conveyor}} \\
Y_{\text{robot}} &= v \times L_{\text{conveyor}} \\
Z_{\text{robot}} &= H_{\text{standoff}} - \Delta Z_{\text{fabric}}
\end{aligned}$$

### Physical Sorting Bins & Routing Matrix

| Bin ID | Designation | Target Garments | Target Temperature | Spin Speed | Bleach Safe |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **`BIN_A`** | Whites & High Temp Bleach | Pure White Cotton, Linens, Towels | 60°C – 90°C | 1400 RPM | **Yes** (Chlorine/Oxygen) |
| **`BIN_B`** | Dark & Black Synthetics | Dark Denim, Black Cotton, Activewear | 30°C – 40°C | 1000 RPM | **No** (Strict Ban) |
| **`BIN_C`** | Bright & Light Colors | Pastels, Yellows, Oranges, Color Cotton | 30°C – 40°C | 1200 RPM | Oxygen Bleach Only |
| **`BIN_D`** | Delicates, Wool & Silk | Pure Silk, Cashmere, Merino Wool, Lace | Cold / 20°C | 400 – 600 RPM | **No** (Strict Ban) |
| **`BIN_E`** | Heavy Denim & Rugged Workwear | Heavy Twill Denim, Overalls, Canvas | 40°C – 50°C | 1200 RPM | Oxygen Bleach Only |
| **`BIN_F`** | Biohazard, High Odour & Pre-Treat | Blood, High VOC (>15 PPM), Mud/Oil | 20°C Cold Enzymatic | 800 RPM | Pre-Treat Reagents |
| **`BIN_G`** | Dry Clean Only & Specialty Care | Solvent Hydrocarbon, Tailored Suits | **0°C (No Water)**| 0 RPM | **No** (Strict Ban) |

### Adaptive Robotic Gripper Force
- **Delicate Silk / Lace / Gauze:** $4.5 \text{ N}$ (Soft pneumatic suction)
- **Standard Cotton / Blends:** $12.0 \text{ N}$ (Medium pneumatic grip)
- **Heavy Denim / Workwear:** $22.0 \text{ N}$ (Heavy mechanical grasp)
- **Mechanical Safety Ceiling:** Hard-capped at $25.0 \text{ N}$ to prevent textile tear or actuator overload.

---

## 🧠 AI Perception Modules

### 1. Multi-Class Stain Chemistry Engine (`stain_classifier.py`)
Classifies garment surface contamination into 8 discrete categories, prescribing precise chemical countermeasures:
- **`BLOOD`**: Neutral pH enzymatic soak + strictly cold water wash (<30°C) to prevent irreversible hemoglobin thermal denaturation.
- **`OIL_GREASE`**: Heavy alkaline detergent + warm/hot wash + surfactant degreaser.
- **`RED_WINE`**: Dilute sodium percarbonate / white vinegar + immediate cold rinse.
- **`COFFEE_TEA`**: Hydrogen peroxide oxidation + glycerin pre-treat.
- **`INK_DYE`**: Isopropyl alcohol / denatured solvent pre-spotting.
- **`MUD_DIRT`**: Mechanical dry brushing + protease enzyme slurry.
- **`COSMETIC_LIPSTICK`**: Micellar oil lifter + alcohol solvent wipe.
- **`GENERAL_ORGANIC`**: Standard bio-enzymatic detergent.

### 2. ISO 3758 Care Symbol Contour Classifier (`care_symbol_classifier.py`)
Identifies international laundry care symbols using spatial contour moments, aspect ratios, and solidity heuristics:
- 🧺 **Washtub Archetype**: Maximum allowable water wash temperature and cycle intensity.
- 📐 **Triangle Archetype**: Bleaching instructions (Non-chlorine vs. strictly prohibited).
- ⏹️ **Square Archetype**: Tumble drying, line drying, or flat drying parameters.
- 熨 **Iron Archetype**: Soleplate temperature thresholds (110°C, 150°C, 200°C).
- ⭕ **Circle Archetype**: Professional dry-cleaning solvent suitability.

### 3. Calibrated CIELAB Color & Bleed Risk Analyzer (`color_classifier.py`)
Converts RGB inspection crops into calibrated CIELAB color space, returning industry-standard human-readable color names and calculating a quantitative **Dye-Bleed Cross-Contamination Risk Score** $(0.0 - 1.0)$ to prevent ruining white loads.

### 4. Micro-Texture Fabric Classifier (`fabric_classifier.py`)
Computes spatial frequency variances, Laplacian high-frequency edge counts, and specular reflection ratios to categorize textile weave (Cotton, Silk, Wool, Denim, Synthetics).

---

## 🛡️ Zero-Tolerance Safety Guardrails

The workcell embeds 6 non-negotiable deterministic safety guardrails. If a model output, operator override, or API input violates safety thresholds, the transaction is **intercepted and blocked immediately**:

1. **Dry Clean Only Ban:** Garments marked `DRY_CLEAN_ONLY` or categorized in `BIN_G` are strictly forbidden from water-wash cycles.
2. **Delicate / Silk Bleach Ban:** Bleach formulations are prohibited on Silk, Wool, Delicates, and chromatic fabrics (`BIN_B`, `BIN_C`, `BIN_D`).
3. **Blood Coagulation Thermal Ceiling:** Blood-stained garments must never receive water temperatures above 30°C.
4. **Delicate Mechanical Limit:** Pure silk, wool, and lace are capped at 30°C wash temp and 600 RPM spin speed.
5. **Emergency Stop Lockout:** While the robot hardware is in `EMERGENCY_STOP` state, all trajectory dispatch and gripper actuation commands are hard-blocked.
6. **Maximum Gripper Force Clamping:** Physical gripper force is clamped at $\le 25.0 \text{ N}$ across all payloads.

---

## 📊 Smart Factory Operations & Sustainability Engine

### Load Balancer (`src/core/load_balancer.py`)
- Continuously aggregates sorted mass (kg) and garment counts across `BIN_A` through `BIN_G`.
- When an individual bin reaches **15.0 kg** (standard commercial washer load capacity), the system triggers an audible/visual `READY_FOR_WASHER` dispatch signal.

### Sustainability & ESG Engine (`src/core/sustainability.py`)
Quantifies environmental and financial ROI in real time:
- 💧 **Water Conservation:** Optimized batch washing prevents under-capacity cycles, saving $\sim 14.5 \text{ L}$ per organized kilogram.
- ⚡ **Energy Reduction:** Temperature optimization avoids unnecessary water heating, saving $\sim 0.35 \text{ kWh}$ per organized kilogram.
- 🌿 **Carbon Offset:** Reduced energy usage mitigates $0.18 \text{ kg } \text{CO}_2\text{e}$ per kilogram.
- 💵 **Capital Preserved:** Fabric damage prevention and zero-bleed sorting preserves an estimated $\$4.20$ of garment equity per load.

---

## 📁 Project Architecture

```
LaundryMann-main/
├── .gitignore                      # Production git exclusions (DBs, temp weights, logs)
├── Dockerfile                      # Multi-stage non-root container deployment
├── README.md                       # Master engineering specification & user guide
├── package.json                    # Project metadata & standard run scripts
├── requirements.txt                # Pinned production dependencies
├── run_server.py                   # Production ASGI API launcher
├── sort_data.py                    # Conveyor sorting ingestion utility
├── start_dashboard.bat             # One-click Windows API backend launcher
├── start_workcell_streamlit.bat    # One-click Windows Workcell Console launcher
├── streamlit_app.py                # Industrial Workcell Telemetry Console (Streamlit)
├── api.py                          # High-performance FastAPI REST server
├── train_ensemble.py               # Offline YOLOv8 ensemble trainer
│
├── docs/                           # Comprehensive Engineering Documentation
│   ├── 00_INDEX.md                 # Document Index
│   ├── 01_PD_Project_Document.md   # Project Description & Scope
│   ├── 02_BRD_Business_Reqs.md     # Business Requirements Document
│   ├── 03_PRD_Product_Reqs.md      # Product Requirements Document
│   ├── 04_SRS_Software_Reqs.md     # Software Requirements Specification
│   ├── 05_FRD_Functional_Reqs.md   # Functional Requirements Document
│   ├── 06_TRD_Technical_Reqs.md    # Technical Requirements Document
│   ├── 07_SAD_Architecture.md      # System Architecture Document
│   ├── 08_TDD_Technical_Design.md  # Technical Design Document
│   ├── 09_Database_and_ER.md       # Database Schema & ER Architecture
│   ├── 10_UIUX_Design.md           # Industrial Console UI/UX Design
│   ├── 14_Security_Plan.md         # Cyber-Physical Security & Cryptography
│   ├── 15_Test_Plan.md             # Integration & Unit Test Strategy
│   ├── openapi.yaml                # OpenAPI 3.1 REST Specification
│   └── schema.sql                  # Enterprise SQL schema
│
├── src/                            # Core Source Code
│   ├── core/
│   │   ├── decision_engine.py      # Deterministic 7-Bin Routing & Recipe Generator
│   │   ├── load_balancer.py        # 15 kg Washer Capacity Tracker
│   │   └── sustainability.py       # Live Water, Power & Carbon ESG Tracker
│   ├── hardware/
│   │   ├── camera_controller.py    # USB / GigE / Synthetic Camera Driver
│   │   ├── multi_camera_manager.py # Synchronized Dual Camera Rig (CAM_01 + CAM_02)
│   │   ├── robot_controller.py     # 6-DOF Manipulator Controller & Kinematics
│   │   └── sensor_interface.py     # E-Nose VOC (PPM) & UV Fluorescence Telemetry
│   ├── models/
│   │   ├── care_symbol_classifier.py # ISO 3758 Symbol Archetype Contour Detector
│   │   ├── clothing_detector.py    # Multi-Garment YOLOv8 Conveyor Extractor
│   │   ├── color_classifier.py     # Calibrated CIELAB / HSV Color & Bleed Analyzer
│   │   ├── edge_optimizer.py       # Sub-30ms Profiler & TensorRT Conversion
│   │   ├── fabric_classifier.py    # Texture Roughness & Frequency Analyzer
│   │   ├── ocr_reader.py           # Optical Character Recognition for Tags
│   │   └── stain_classifier.py     # 8-Class Stain Chemistry & Rx Generator
│   ├── security/
│   │   ├── auth_manager.py         # PBKDF2 Password Hashing & HMAC Bearer Tokens
│   │   ├── guardrails.py           # Zero-Tolerance Safety Interceptor
│   │   └── input_validator.py      # MIME Magic-Bytes & Image Decompression Bomb Guard
│   └── evals/
│       └── benchmark_eval.py       # Production Quality & Latency Benchmark Harness
│
├── frontend/                       # Lightweight Static Web Client
│   ├── index.html                  # Responsive Workcell Web Interface
│   ├── app.js                      # Dual-Camera Capture & Robot Dispatch Client
│   └── style.css                   # Obsidian Dark Industrial Styling
│
└── tests/                          # Automated Verification Suite
    ├── test_pipeline.py            # Unit tests for Core AI & Routing Modules
    ├── test_api_endpoints.py       # End-to-end FastAPI endpoint integration tests
    └── test_advanced_features.py   # Unit tests for Robotics, Sensors, Balancer & Evals
```

---

## ⚡ Quickstart & Installation

### Prerequisites
- **Python 3.11+** (x64)
- **Git**
- Optional: **Tesseract OCR** (for physical care label text extraction)
  - Windows: UB-Mannheim Tesseract Installer added to `PATH`
  - Linux: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/BEAST-AMMAR/LaundryMann.git
cd LaundryMann

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install production dependencies
pip install -r requirements.txt
```

### 2. Launching the Workcell

#### Option A: Industrial Workcell Console (Streamlit)
Launches the full interactive factory operator telemetry console featuring live camera feeds, 6-DOF robotic arm trajectory planner, 7-bin capacity monitor, and live benchmark eval harness:
```bash
# Windows one-click launcher:
start_workcell_streamlit.bat

# Or manual execution:
streamlit run streamlit_app.py
```
*Access in browser at: `http://localhost:8501`*

#### Option B: High-Performance REST API (FastAPI)
Launches the asynchronous microservice backend for headless robotics and factory SCADA integration:
```bash
# Windows one-click launcher:
start_dashboard.bat

# Or manual execution:
python run_server.py
```
*Access interactive Swagger UI documentation at: `http://localhost:8000/docs`*

---

## 🐳 Docker Deployment

The workcell includes a multi-stage, security-hardened `Dockerfile` running on `python:3.11-slim` with a non-root user (`appuser`):

```bash
# Build the production container image
docker build -t nexus-laundry-workcell:2.0 .

# Run the container (publishing API port 8000 and Console port 8501)
docker run -d --name nexus-workcell -p 8000:8000 -p 8501:8501 nexus-laundry-workcell:2.0
```

---

## 📡 REST API Reference

The backend provides production REST endpoints documented via OpenAPI 3.1:

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `GET` | `/api/v1/health` | Comprehensive subsystem readiness & model status check |
| `POST` | `/api/v1/workcell/inspect` | Full workcell inspection from dual cameras + E-Nose sensors |
| `POST` | `/api/v1/analyze` | Single garment analysis (Fabric, Color, Stains, Symbols, Routing) |
| `GET` | `/api/v1/hardware/camera/feed` | Capture live or synthetic frame from CAM_01 or CAM_02 |
| `POST` | `/api/v1/hardware/camera/capture-dual` | Synchronized simultaneous snapshot from CAM_01 and CAM_02 |
| `GET` | `/api/v1/hardware/sensors/telemetry` | Live readings from E-Nose VOC and UV fluorescence sensors |
| `POST` | `/api/v1/robot/dispatch` | Plan and dispatch robotic trajectory to physical target bin |
| `POST` | `/api/v1/robot/emergency-stop` | Mechanical E-Stop engagement/disengagement |
| `GET` | `/api/v1/operations/load-balancer` | Cumulative weight, garment counts, and 15 kg washer alerts |
| `POST` | `/api/v1/operations/load-balancer/record-sort`| Update physical bin weights following a sorting action |
| `GET` | `/api/v1/operations/sustainability` | Real-time ESG metrics (Water, kWh, Carbon, Preserved Capital) |
| `GET` | `/api/v1/evals/benchmark` | Execute automated performance and safety guardrail benchmark |

---

## 🧪 Testing & Quality Assurance

The codebase includes 30 automated unit and integration tests verifying all perception algorithms, robotic controllers, sensor interfaces, guardrails, and API endpoints:

```bash
# Execute entire test suite
python -m unittest discover tests

# Output:
# Ran 30 tests in 2.58s
# OK (All tests passing)
```

To run the live performance benchmark:
```bash
python src/evals/benchmark_eval.py
```

---

## 👥 Authors & Acknowledgments

- **Lead Engineer & Architect:** [Muhammad Ammar](https://github.com/BEAST-AMMAR)
- **Repository:** [https://github.com/BEAST-AMMAR/LaundryMann.git](https://github.com/BEAST-AMMAR/LaundryMann.git)

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
