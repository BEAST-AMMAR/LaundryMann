from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import numpy as np
from PIL import Image
import io
import asyncio
import concurrent.futures
from contextlib import asynccontextmanager
import threading
import base64
import time
from typing import Optional, List

from src.models.stain_detector import StainDetector
from src.models.stain_classifier import StainClassifier
from src.models.fabric_classifier import FabricClassifier
from src.models.color_classifier import ColorClassifier
from src.models.care_symbol_classifier import CareSymbolClassifier
from src.core.decision_engine import LaundryDecisionEngine
from src.core.load_balancer import WorkcellLoadBalancer
from src.core.sustainability import SustainabilityEngine
from src.models.ocr_reader import OCRReader
from src.models.clothing_detector import ClothingDetector
from src.database import get_db, WardrobeItem, User
from src.hardware.camera_controller import HardwareCameraController
from src.hardware.multi_camera_manager import MultiCameraManager
from src.hardware.robot_controller import RoboticArmController
from src.hardware.sensor_interface import HardwareSensorInterface
from src.security import SecurityValidator, SafetyGuardrails, SecurityAuthManager
from src.evals import WorkcellBenchmarkHarness

# Global references
stain_detector = None
stain_classifier = None
fabric_classifier = None
color_classifier = None
care_symbol_classifier = None
decision_engine = None
load_balancer = None
sustainability_engine = None
ocr_reader = None
clothing_detector = None
camera_controller = None
multi_camera = None
robot_controller = None
sensor_interface = None
auth_manager = None
benchmark_harness = None
executor = None
is_ready = False

def load_subsystems():
    global stain_detector, stain_classifier, fabric_classifier, color_classifier, care_symbol_classifier
    global decision_engine, load_balancer, sustainability_engine, ocr_reader, clothing_detector
    global camera_controller, multi_camera, robot_controller, sensor_interface
    global auth_manager, benchmark_harness, executor, is_ready

    if is_ready:
        return

    print("[NEXUS Subsystems] Initializing Perception, Hardware, Robotics, & Operations...")
    try:
        # AI Models
        stain_detector = StainDetector()
        stain_classifier = StainClassifier()
        fabric_classifier = FabricClassifier()
        color_classifier = ColorClassifier()
        care_symbol_classifier = CareSymbolClassifier()
        decision_engine = LaundryDecisionEngine()
        ocr_reader = OCRReader()
        clothing_detector = ClothingDetector()

        # Operational & Sustainability Engines
        load_balancer = WorkcellLoadBalancer()
        sustainability_engine = SustainabilityEngine()

        # Security & Benchmarking
        auth_manager = SecurityAuthManager()
        benchmark_harness = WorkcellBenchmarkHarness()

        # Hardware & Robotics Workcell
        camera_controller = HardwareCameraController()
        multi_camera = MultiCameraManager()
        robot_controller = RoboticArmController()
        sensor_interface = HardwareSensorInterface()

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        is_ready = True
        print("[NEXUS Subsystems] All AI Models, Robotics & Operational Engines ONLINE!")
    except Exception as e:
        print("[NEXUS Subsystems] Failed to initialize subsystems:", e)

def ensure_subsystems():
    if not is_ready:
        load_subsystems()

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_subsystems()
    yield
    print("[NEXUS Subsystems] Shutting down...")
    if multi_camera:
        multi_camera.shutdown()
    if camera_controller:
        camera_controller.shutdown()
    if executor:
        executor.shutdown(wait=True)

app = FastAPI(
    title="NEXUS Autonomous Laundry Workcell API",
    description="Industrial sorting station: multi-camera optical inspection, multi-model AI ensemble, sustainability analytics, and robotic pick-and-place control.",
    version="4.0.0",
    lifespan=lifespan
)

def encode_image(img_array: np.ndarray) -> Optional[str]:
    try:
        pil_img = Image.fromarray(img_array)
        buffered = io.BytesIO()
        pil_img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception:
        return None

# =============================================================================
# HEALTH & READINESS ENDPOINTS
# =============================================================================

@app.get("/health/ready")
def check_readiness():
    ensure_subsystems()
    return {
        "status": "ready" if is_ready else "initializing",
        "timestamp": time.time(),
        "subsystems": {
            "ai_models_loaded": is_ready,
            "camera_connected": camera_controller.is_connected if camera_controller else False,
            "robot_state": robot_controller.current_state if robot_controller else "OFFLINE",
            "sensor_telemetry_active": sensor_interface is not None,
            "load_balancer_active": load_balancer is not None,
            "sustainability_engine_active": sustainability_engine is not None
        }
    }

# =============================================================================
# HARDWARE CAMERA & MULTI-OPTICS ENDPOINTS
# =============================================================================

@app.get("/hardware/camera/stream")
def stream_hardware_camera():
    """Live MJPEG video stream from the overhead inspection camera."""
    ensure_subsystems()
    if not camera_controller:
        raise HTTPException(status_code=503, detail="Camera controller offline")
    return StreamingResponse(
        camera_controller.generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/hardware/camera/capture")
def capture_camera_frame():
    """Triggers an instantaneous high-res snapshot from the overhead inspection camera."""
    ensure_subsystems()
    if not camera_controller:
        raise HTTPException(status_code=503, detail="Camera controller offline")
    frame = camera_controller.capture_snapshot()
    img_b64 = encode_image(frame)
    return {
        "status": "success",
        "diagnostics": camera_controller.get_diagnostics(),
        "image_base64": img_b64
    }

@app.get("/hardware/camera/macro_tag")
def capture_macro_tag():
    """Captures a dedicated high-magnification optical frame from CAM_02 for care label analysis."""
    ensure_subsystems()
    if not multi_camera:
        raise HTTPException(status_code=503, detail="Multi-camera manager offline")
    frame = multi_camera.capture_macro_tag_frame()
    img_b64 = encode_image(frame)
    return {
        "status": "success",
        "camera": "CAM_02_MACRO_TAG",
        "image_base64": img_b64
    }

@app.get("/hardware/sensors")
def get_sensor_telemetry():
    """Returns real-time telemetry from E-Nose VOC and UV multispectral sensors."""
    ensure_subsystems()
    if not sensor_interface:
        raise HTTPException(status_code=503, detail="Sensor interface offline")
    return sensor_interface.get_telemetry()

@app.post("/hardware/sensors/trigger_test")
def trigger_sensor_test(voc_ppm: float = Form(120.0), uv_index: float = Form(55.0)):
    ensure_subsystems()
    if sensor_interface:
        sensor_interface.set_sensor_overrides(voc_ppm, uv_index)
    return {"status": "success", "applied_voc_ppm": voc_ppm, "applied_uv_index": uv_index}

@app.post("/hardware/sensors/reset")
def reset_sensors():
    ensure_subsystems()
    if sensor_interface:
        sensor_interface.reset_ambient()
    return {"status": "success", "message": "Sensors reset to baseline ambient levels"}

# =============================================================================
# ROBOTIC ARM CONTROL & TELEMETRY
# =============================================================================

@app.get("/robot/status")
def get_robot_status():
    ensure_subsystems()
    if not robot_controller:
        raise HTTPException(status_code=503, detail="Robotic controller offline")
    return robot_controller.get_status()

@app.post("/robot/emergency_stop")
def trigger_e_stop(stop: bool = Form(True)):
    ensure_subsystems()
    if not robot_controller:
        raise HTTPException(status_code=503, detail="Robotic controller offline")
    robot_controller.trigger_emergency_stop(stop)
    return {"status": "success", "emergency_stop": stop}

@app.post("/robot/dispatch")
def dispatch_robot_action(bin_id: str = Form(...), fabric: str = Form("Cotton")):
    ensure_subsystems()
    if not robot_controller:
        raise HTTPException(status_code=503, detail="Robotic controller offline")
    
    # Validate with safety guardrail before physical actuation
    bbox = [400, 250, 880, 500]
    grasp_params = robot_controller.compute_grasp_parameters(bbox, fabric)
    is_safe, msg = SafetyGuardrails.validate_robot_trajectory(grasp_params, robot_controller.emergency_stop)
    if not is_safe:
        raise HTTPException(status_code=400, detail=msg)

    packet = robot_controller.dispatch_pick_and_place(bbox, bin_id, fabric)
    return {"status": "success", "dispatch_packet": packet}

# =============================================================================
# INFERENCE, STAIN CHEMISTRY & ROBOTIC ROUTING PIPELINE
# =============================================================================

@app.post("/analyze")
async def analyze_garment(
    file: Optional[UploadFile] = File(None),
    odor_detected: bool = Form(False),
    uv_fluorescence: bool = Form(False),
    auto_robot_dispatch: bool = Form(False),
    tag_file: Optional[UploadFile] = File(None)
):
    """
    Analyzes a garment image with multi-class stain classification, chemical prescriptions,
    safety guardrails, bin load tracking, and sustainability calculation.
    """
    ensure_subsystems()

    # 1. Input Validation & EXIF Sanitization Guard
    if file is not None:
        contents = await file.read()
        is_valid, sanitized_array, err = SecurityValidator.validate_and_sanitize_image(contents)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Image Validation Error: {err}")
        img_array = sanitized_array
    else:
        # Capture directly from physical overhead camera
        if not camera_controller:
            raise HTTPException(status_code=503, detail="Camera controller offline")
        img_array = camera_controller.capture_snapshot()

    # Optional Care Tag OCR & Symbol Constraints
    ocr_constraints = []
    if tag_file is not None:
        tag_contents = await tag_file.read()
        t_valid, t_img, _ = SecurityValidator.validate_and_sanitize_image(tag_contents)
        if t_valid:
            tag_report = ocr_reader.extract_structured_tag(t_img)
            ocr_constraints = tag_report["parsed_instructions"]

    # Read hardware sensors if not overridden
    if sensor_interface:
        telemetry = sensor_interface.get_telemetry()
        if not odor_detected:
            odor_detected = telemetry["voc_e_nose"]["hazard_flag"]
        if not uv_fluorescence:
            uv_fluorescence = telemetry["uv_multispectral"]["invisible_stain_detected"]

    loop = asyncio.get_event_loop()
    stain_task = loop.run_in_executor(executor, stain_detector.detect_stains, img_array)
    fabric_task = loop.run_in_executor(executor, fabric_classifier.predict_fabric, img_array)
    color_task = loop.run_in_executor(executor, color_classifier.analyze_color_profile, img_array)

    stain_result, fabric_result, color_result = await asyncio.gather(stain_task, fabric_task, color_task)

    raw_stains, annotated_img = stain_result
    fabric_label, fabric_conf = fabric_result
    color_profile = color_result

    # 2. Multi-Class Stain Chemistry Classification & Prescription
    enriched_stains = stain_classifier.enrich_detected_stains(img_array, raw_stains)

    # 3. Industrial Decision Engine
    decision_packet = decision_engine.decide_industrial_routing(
        color=color_profile["category"],
        fabric=fabric_label,
        stains=enriched_stains,
        odor_detected=odor_detected,
        uv_fluorescence=uv_fluorescence,
        ocr_constraints=ocr_constraints,
        color_name=color_profile["color_name"],
        bleed_risk=color_profile["bleed_risk"]
    )

    # 4. Zero-Tolerance Safety Guardrails Verification
    is_safe, violations = SafetyGuardrails.validate_wash_decision(
        decision=decision_packet,
        fabric=fabric_label,
        color_category=color_profile["category"],
        stains=enriched_stains,
        ocr_rules=ocr_constraints
    )
    if not is_safe:
        # Override decision with safety fallback
        decision_packet["bin_id"] = "BIN_G"
        decision_packet["bin_name"] = "Manual Inspection (Guardrail Intercepted)"
        decision_packet["alerts"].extend(violations)

    # 5. Compute Robotic Arm Grasp Targets
    h, w = img_array.shape[:2]
    garment_bbox = [int(w * 0.2), int(h * 0.2), int(w * 0.8), int(h * 0.8)]
    grasp_parameters = robot_controller.compute_grasp_parameters(garment_bbox, fabric_label)

    # 6. Update Bin Capacity & Load Balancer
    bin_load_status = load_balancer.route_item_to_bin(
        bin_id=decision_packet["bin_id"],
        fabric=fabric_label,
        item_desc=f"{color_profile['color_name']} {fabric_label}",
        bbox=garment_bbox
    )

    # 7. Update Sustainability & Chemical ROI Metrics
    sustainability_impact = sustainability_engine.record_sorting_event(
        color=color_profile["category"],
        fabric=fabric_label,
        stains_count=len(enriched_stains),
        routed_bin=decision_packet["bin_id"],
        garment_weight_kg=bin_load_status["added_weight_kg"]
    )

    # 8. Optional Auto-Dispatch
    dispatch_telemetry = None
    if auto_robot_dispatch and robot_controller:
        # Check guardrail before actuation
        g_safe, _ = SafetyGuardrails.validate_robot_trajectory(grasp_parameters, robot_controller.emergency_stop)
        if g_safe:
            dispatch_telemetry = robot_controller.dispatch_pick_and_place(
                bbox=garment_bbox,
                bin_id=decision_packet["bin_id"],
                fabric=fabric_label,
                item_label=f"{color_profile['color_name']} {fabric_label}"
            )

    img_base64 = encode_image(annotated_img)

    return JSONResponse(content={
        "status": "success",
        "annotated_image": img_base64,
        "analysis": {
            "color": {
                "prediction": color_profile["category"],
                "color_name": color_profile["color_name"],
                "bleed_risk": color_profile["bleed_risk"],
                "dominant_hex": color_profile["hex"],
                "confidence": color_profile["confidence"]
            },
            "fabric": {
                "prediction": fabric_label,
                "confidence": fabric_conf
            },
            "stains_detected": len(enriched_stains),
            "stain_details": enriched_stains
        },
        "sensors": {
            "odor_detected": odor_detected,
            "uv_fluorescence_detected": uv_fluorescence
        },
        "decision": {
            "routing_bin": decision_packet["bin_id"],
            "bin_name": decision_packet["bin_name"],
            "instructions": decision_packet["instructions"],
            "recipe": decision_packet["recipe"],
            "reasons": decision_packet["reasons"],
            "alerts": decision_packet["alerts"],
            "guardrail_verified": is_safe
        },
        "robotics": {
            "grasp_parameters": grasp_parameters,
            "target_drop_coords": decision_packet["robot_target_coords"],
            "auto_dispatched": auto_robot_dispatch,
            "dispatch_telemetry": dispatch_telemetry
        },
        "operations": {
            "bin_load": bin_load_status,
            "sustainability": sustainability_impact
        }
    })

@app.post("/analyze_basket")
async def analyze_basket(file: Optional[UploadFile] = File(None)):
    """
    Scans multiple garments on conveyor belt with cross-contamination check,
    individual robotic grasp targets, and sustainability tracking.
    """
    ensure_subsystems()

    if file is not None:
        contents = await file.read()
        is_valid, sanitized_array, _ = SecurityValidator.validate_and_sanitize_image(contents)
        img_array = sanitized_array if is_valid else np.array(Image.open(io.BytesIO(contents)).convert('RGB'))
    else:
        if not camera_controller:
            raise HTTPException(status_code=503, detail="Camera controller offline")
        img_array = camera_controller.capture_snapshot()

    garments = clothing_detector.extract_garments_with_metadata(img_array)
    results = []

    for item in garments:
        crop = item["crop"]
        raw_stains, _ = stain_detector.detect_stains(crop)
        enriched_stains = stain_classifier.enrich_detected_stains(crop, raw_stains)
        fabric_label, fabric_conf = fabric_classifier.predict_fabric(crop)
        color_profile = color_classifier.analyze_color_profile(crop)

        grasp = robot_controller.compute_grasp_parameters(item["bbox"], fabric_label)
        decision = decision_engine.decide_industrial_routing(
            color=color_profile["category"],
            fabric=fabric_label,
            stains=enriched_stains,
            color_name=color_profile["color_name"],
            bleed_risk=color_profile["bleed_risk"]
        )

        results.append({
            "bbox": item["bbox"],
            "centroid": item["centroid"],
            "color": color_profile["category"],
            "color_name": color_profile["color_name"],
            "bleed_risk": color_profile["bleed_risk"],
            "fabric": fabric_label,
            "stains": len(enriched_stains),
            "stain_details": enriched_stains,
            "target_bin": decision["bin_id"],
            "bin_name": decision["bin_name"],
            "pick_coords_mm": grasp["pick_coords_mm"]
        })

    safety_report = clothing_detector.check_mixed_safety(results)
    if "Color Bleed Hazard" in safety_report:
        sustainability_engine.record_bleed_hazard_prevented(count=len(results))

    return JSONResponse(content={
        "status": "success",
        "items_detected": len(garments),
        "items": results,
        "safety_report": safety_report
    })

@app.post("/analyze_tag_symbols")
async def analyze_tag_symbols(file: Optional[UploadFile] = File(None)):
    """
    Analyzes care tags using ISO 3758 symbol vision classification + OCR.
    """
    ensure_subsystems()

    if file is not None:
        contents = await file.read()
        is_valid, sanitized_array, _ = SecurityValidator.validate_and_sanitize_image(contents)
        img_array = sanitized_array if is_valid else np.array(Image.open(io.BytesIO(contents)).convert('RGB'))
    else:
        # Capture from macro optical camera CAM_02
        img_array = multi_camera.capture_macro_tag_frame()

    symbol_report = care_symbol_classifier.classify_tag_symbols(img_array)
    ocr_report = ocr_reader.extract_structured_tag(img_array)

    return JSONResponse(content={
        "status": "success",
        "symbol_classification": symbol_report,
        "ocr_text": ocr_report["raw_text"],
        "combined_restrictions": list(set(symbol_report["restrictions"] + ocr_report["parsed_instructions"]))
    })

# =============================================================================
# SMART FACTORY & COMMERCIAL OPERATIONS ENDPOINTS
# =============================================================================

@app.get("/load_balancer/status")
def get_load_balancer_status():
    """Returns current real-time capacity and weight distribution of all 7 bins."""
    ensure_subsystems()
    return load_balancer.get_workcell_capacity_summary()

@app.post("/load_balancer/unload")
def unload_bin(bin_id: str = Form(...)):
    """Unloads bin into industrial washing machine and resets weight."""
    ensure_subsystems()
    return load_balancer.unload_bin_to_washer(bin_id)

@app.get("/sustainability/metrics")
def get_sustainability_metrics():
    """Returns environmental impact (Water, Energy, Carbon) and financial savings."""
    ensure_subsystems()
    return sustainability_engine.get_summary()

@app.get("/evals/benchmark")
def run_benchmark():
    """Executes full automated evaluation benchmark suite and returns scorecard."""
    ensure_subsystems()
    return benchmark_harness.run_full_benchmark_suite()

# =============================================================================
# WARDROBE & AUDIT LOGS
# =============================================================================

@app.post("/wardrobe/add")
async def add_to_wardrobe(
    color: str = Form(...),
    fabric: str = Form(...),
    stain_status: str = Form(...),
    wash_instructions: str = Form(...),
    db: Session = Depends(get_db)
):
    item = WardrobeItem(
        color=SecurityValidator.sanitize_string(color),
        fabric=SecurityValidator.sanitize_string(fabric),
        stain_status=SecurityValidator.sanitize_string(stain_status),
        wash_instructions=SecurityValidator.sanitize_string(wash_instructions)
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"status": "success", "item_id": item.id}

@app.get("/wardrobe/list")
async def list_wardrobe(db: Session = Depends(get_db)):
    items = db.query(WardrobeItem).order_by(WardrobeItem.date_added.desc()).all()
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "color": item.color,
            "fabric": item.fabric,
            "stains": item.stain_status,
            "instructions": item.wash_instructions,
            "date_added": item.date_added.isoformat()
        })
    return {"status": "success", "items": result}

# Mount static frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
