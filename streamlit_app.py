import streamlit as st
import cv2
import numpy as np
from PIL import Image
import os
import io
import time
from typing import Dict, Any, List

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
from src.hardware.camera_controller import HardwareCameraController
from src.hardware.multi_camera_manager import MultiCameraManager
from src.hardware.robot_controller import RoboticArmController
from src.hardware.sensor_interface import HardwareSensorInterface
from src.security import SafetyGuardrails, SecurityValidator
from src.evals import WorkcellBenchmarkHarness
from src.utils.pdf_generator import generate_care_pdf
from src.database import get_db, WardrobeItem, User

# =============================================================================
# WORKCELL PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="NEXUS · Industrial Robotic Laundry Workcell",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# DARK INDUSTRIAL ENTERPRISE THEME
# =============================================================================
def get_industrial_theme_css():
    return """<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-base: #0A0B0E;
        --bg-panel: #111318;
        --bg-card: rgba(255, 255, 255, 0.025);
        --bg-card-hover: rgba(255, 255, 255, 0.045);
        --border: rgba(255, 255, 255, 0.09);
        --accent-cyan: #06B6D4;
        --accent-purple: #8B5CF6;
        --accent-emerald: #10B981;
        --accent-amber: #F59E0B;
        --accent-rose: #F43F5E;
        --text-primary: #F3F4F6;
        --text-secondary: #9CA3AF;
        --text-muted: #6B7280;
    }

    #MainMenu, footer, header, .stDeployButton { visibility: hidden; display: none; }

    html, body, .stApp {
        font-family: 'Inter', sans-serif !important;
        background-color: var(--bg-base) !important;
        color: var(--text-primary);
        letter-spacing: -0.01em;
    }

    section[data-testid="stSidebar"] {
        background-color: var(--bg-panel) !important;
        border-right: 1px solid var(--border) !important;
    }

    .nx-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        background: var(--bg-panel);
        border: 1px solid var(--border);
        border-radius: 12px;
        margin-bottom: 20px;
    }

    .nx-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        text-transform: uppercase;
    }
    .nx-badge-active { background: rgba(16, 185, 129, 0.12); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .nx-badge-alert { background: rgba(244, 63, 94, 0.12); color: #F43F5E; border: 1px solid rgba(244, 63, 94, 0.3); }
    .nx-badge-cyan { background: rgba(6, 182, 212, 0.12); color: #06B6D4; border: 1px solid rgba(6, 182, 212, 0.3); }

    .nx-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .nx-card-title {
        font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-secondary);
        text-transform: uppercase;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .bin-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-top: 10px;
    }
    .bin-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px;
        transition: all 0.2s ease;
    }
    .bin-card:hover {
        border-color: var(--accent-cyan);
        transform: translateY(-2px);
    }
    .bin-card-highlight {
        border-color: var(--accent-cyan) !important;
        background: rgba(6, 182, 212, 0.08) !important;
        box-shadow: 0 0 15px rgba(6, 182, 212, 0.2);
    }
    .bin-code { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: var(--accent-cyan); }
    .bin-name { font-size: 0.78rem; color: var(--text-secondary); margin-top: 4px; }
    .bin-count { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--text-muted); margin-top: 6px; }

    .stButton > button {
        background: rgba(6, 182, 212, 0.15) !important;
        border: 1px solid var(--accent-cyan) !important;
        color: #E0F2FE !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'JetBrains Mono', monospace !important;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: var(--accent-cyan) !important;
        color: #000 !important;
        box-shadow: 0 0 16px rgba(6, 182, 212, 0.4);
    }
    </style>"""

st.markdown(get_industrial_theme_css(), unsafe_allow_html=True)

# =============================================================================
# SUBSYSTEM INITIALIZATION
# =============================================================================
@st.cache_resource
def init_workcell():
    stain_detector = StainDetector()
    stain_classifier = StainClassifier()
    fabric_classifier = FabricClassifier()
    color_classifier = ColorClassifier()
    care_symbol_classifier = CareSymbolClassifier()
    decision_engine = LaundryDecisionEngine()
    load_balancer = WorkcellLoadBalancer()
    sustainability_engine = SustainabilityEngine()
    ocr_reader = OCRReader()
    clothing_detector = ClothingDetector()
    camera_controller = HardwareCameraController()
    multi_camera = MultiCameraManager()
    robot_controller = RoboticArmController()
    sensor_interface = HardwareSensorInterface()
    benchmark_harness = WorkcellBenchmarkHarness()
    return (
        stain_detector, stain_classifier, fabric_classifier, color_classifier,
        care_symbol_classifier, decision_engine, load_balancer, sustainability_engine,
        ocr_reader, clothing_detector, camera_controller, multi_camera,
        robot_controller, sensor_interface, benchmark_harness
    )

(
    stain_detector, stain_classifier, fabric_classifier, color_classifier,
    care_symbol_classifier, decision_engine, load_balancer, sustainability_engine,
    ocr_reader, clothing_detector, camera_controller, multi_camera,
    robot_controller, sensor_interface, benchmark_harness
) = init_workcell()

if "operator_logged_in" not in st.session_state:
    st.session_state.operator_logged_in = True
    st.session_state.operator_name = "Chief Sorting Engineer"
    st.session_state.operator_id = 1
if "last_analysis_result" not in st.session_state:
    st.session_state.last_analysis_result = None

# =============================================================================
# SIDEBAR: WORKCELL CONTROLS & HARDWARE TELEMETRY
# =============================================================================
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #06B6D4;">NEXUS ROBOTICS</span><br>
        <span style="font-size: 0.75rem; color: #9CA3AF;">Autonomous Sorting Workcell #4</span>
    </div>
    """, unsafe_allow_html=True)

    app_mode = st.radio(
        "WORKCELL CONSOLE",
        [
            "Inspection Workcell (Camera & Robot)",
            "Conveyor Batch Sorter",
            "Care Tag Optical Scanner (ISO 3758)",
            "Smart Factory Load Balancer & Sustainability",
            "Factory Batch Telemetry & Wardrobe",
            "System Diagnostics & Evals Benchmark"
        ]
    )

    st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 20px 0;'>", unsafe_allow_html=True)

    telemetry = sensor_interface.get_telemetry()
    robot_status = robot_controller.get_status()
    cam_diag = camera_controller.get_diagnostics()
    sust_summary = sustainability_engine.get_summary()

    st.markdown("<div class='nx-card-title'>Live Sensors & VOC</div>", unsafe_allow_html=True)
    
    voc_val = telemetry['voc_e_nose']['ppm']
    voc_color = "#F43F5E" if telemetry['voc_e_nose']['hazard_flag'] else "#10B981"
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 10px; margin-bottom: 10px;">
        <div style="font-size: 0.7rem; color: #9CA3AF;">E-NOSE VOC SENSOR</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; font-weight: 700; color: {voc_color};">{voc_val} PPM</div>
        <div style="font-size: 0.68rem; color: #6B7280;">{telemetry['voc_e_nose']['status']}</div>
    </div>
    """, unsafe_allow_html=True)

    uv_idx = telemetry['uv_multispectral']['fluorescence_idx']
    uv_color = "#8B5CF6" if telemetry['uv_multispectral']['invisible_stain_detected'] else "#10B981"
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 10px; margin-bottom: 10px;">
        <div style="font-size: 0.7rem; color: #9CA3AF;">UV MULTISPECTRAL STROBE</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; font-weight: 700; color: {uv_color};">{uv_idx} INDEX</div>
        <div style="font-size: 0.68rem; color: #6B7280;">{telemetry['uv_multispectral']['status']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Live Sustainability Snapshot
    st.markdown(f"""
    <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px; padding: 10px; margin-bottom: 12px;">
        <div style="font-size: 0.7rem; color: #10B981; font-weight: 600;">ESG & RESOURCE SAVINGS</div>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; font-weight: 700; color: #FFF; margin-top: 2px;">💧 {sust_summary['water_saved_liters']} L Water</div>
        <div style="font-size: 0.75rem; color: #9CA3AF;">⚡ {sust_summary['energy_saved_kwh']} kWh | 💵 ${sust_summary['financial_capital_saved_usd']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Sensor Test Controls
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("Spike VOC (Odor)"):
            sensor_interface.trigger_voc_spike(125.0)
            st.rerun()
    with col_s2:
        if st.button("Trigger UV Stain"):
            sensor_interface.trigger_uv_fluorescence(60.0)
            st.rerun()

    if st.button("Reset Sensors to Ambient"):
        sensor_interface.reset_ambient()
        st.rerun()

    st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 20px 0;'>", unsafe_allow_html=True)

    if robot_status["emergency_stop"]:
        if st.button("🔴 RESET EMERGENCY STOP", use_container_width=True):
            robot_controller.trigger_emergency_stop(False)
            st.rerun()
    else:
        if st.button("⚠️ TRIGGER ROBOT E-STOP", use_container_width=True):
            robot_controller.trigger_emergency_stop(True)
            st.rerun()

    st.caption("NEXUS Enterprise Workcell OS v4.0 · 2026")

# =============================================================================
# HEADER BAR
# =============================================================================
robot_badge = "nx-badge-active" if not robot_status["emergency_stop"] else "nx-badge-alert"
robot_state_txt = robot_status["arm_state"] if not robot_status["emergency_stop"] else "EMERGENCY STOPPED"
cam_txt = "CAM_01 LIVE" if cam_diag["is_connected"] else "CONVEYOR SIMULATOR"

st.markdown(f"""
<div class="nx-header">
    <div>
        <h2 style="margin: 0; font-size: 1.3rem; font-weight: 700; color: #F3F4F6;">Autonomous Sorting Workcell</h2>
        <div style="font-size: 0.8rem; color: #9CA3AF; margin-top: 4px;">Station 04 Overhead Optics, Tag Macro Scanner, & 6-DOF Robotic Manipulator</div>
    </div>
    <div style="display: flex; gap: 12px; align-items: center;">
        <span class="nx-badge nx-badge-cyan">📹 {cam_txt}</span>
        <span class="nx-badge {robot_badge}">🤖 ARM: {robot_state_txt}</span>
        <span class="nx-badge nx-badge-active">CYCLES: {robot_status['total_cycles_completed']}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# 1. INSPECTION WORKCELL (CAMERA, MULTI-CLASS STAINS & ROBOT)
# =============================================================================
if app_mode == "Inspection Workcell (Camera & Robot)":
    col_cam, col_robot = st.columns([1.3, 1], gap="medium")

    with col_cam:
        st.markdown("<div class='nx-card-title'>📷 Overhead Inspection Camera Feed</div>", unsafe_allow_html=True)
        
        input_source = st.radio("Optics Source", ["Overhead Camera (CAM_01 Direct)", "Manual Upload / High-Res Frame"], horizontal=True)

        img_for_inference = None
        if input_source == "Overhead Camera (CAM_01 Direct)":
            frame = camera_controller.get_frame()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.image(frame_rgb, use_column_width=True, caption=f"Overhead Conveyor Feed · 1080p · {cam_diag['fps']} FPS")
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("⚡ Trigger Inspection Scan", use_container_width=True):
                    img_for_inference = frame_rgb
            with c_btn2:
                uv_toggle = st.checkbox("Engage 365nm UV Strobe", value=camera_controller.uv_mode)
                camera_controller.set_uv_mode(uv_toggle)

        else:
            uploaded = st.file_uploader("Upload Garment Frame", type=["jpg", "jpeg", "png"])
            if uploaded:
                raw_b = uploaded.read()
                is_v, san_img, _ = SecurityValidator.validate_and_sanitize_image(raw_b)
                img_for_inference = san_img if is_v else np.array(Image.open(io.BytesIO(raw_b)).convert('RGB'))
                st.image(img_for_inference, use_column_width=True, caption="Uploaded Garment Inspection Frame")

        if img_for_inference is not None:
            with st.spinner("Executing Multi-Model Perception, Chemical Stain Classification, & Grasp Trajectory..."):
                start_t = time.time()
                
                # 1. Perception
                raw_stains, annotated_img = stain_detector.detect_stains(img_for_inference)
                enriched_stains = stain_classifier.enrich_detected_stains(img_for_inference, raw_stains)
                fabric_name, fabric_conf = fabric_classifier.predict_fabric(img_for_inference)
                color_profile = color_classifier.analyze_color_profile(img_for_inference)
                
                # Sensor states
                telemetry = sensor_interface.get_telemetry()
                odor_flag = telemetry["voc_e_nose"]["hazard_flag"]
                uv_flag = telemetry["uv_multispectral"]["invisible_stain_detected"]
                
                # 2. Decision Engine
                decision = decision_engine.decide_industrial_routing(
                    color=color_profile["category"],
                    fabric=fabric_name,
                    stains=enriched_stains,
                    odor_detected=odor_flag,
                    uv_fluorescence=uv_flag,
                    color_name=color_profile["color_name"],
                    bleed_risk=color_profile["bleed_risk"]
                )

                # 3. Zero-Tolerance Guardrail Verification
                is_safe, guard_violations = SafetyGuardrails.validate_wash_decision(
                    decision=decision,
                    fabric=fabric_name,
                    color_category=color_profile["category"],
                    stains=enriched_stains
                )

                # 4. Robotic Arm Grasp Trajectory
                h, w = img_for_inference.shape[:2]
                target_bbox = [int(w * 0.2), int(h * 0.2), int(w * 0.8), int(h * 0.8)]
                grasp = robot_controller.compute_grasp_parameters(target_bbox, fabric_name)

                # 5. Load Balancer & Sustainability Recording
                bin_load = load_balancer.route_item_to_bin(
                    bin_id=decision["bin_id"],
                    fabric=fabric_name,
                    item_desc=f"{color_profile['color_name']} {fabric_name}",
                    bbox=target_bbox
                )
                sustainability_engine.record_sorting_event(
                    color=color_profile["category"],
                    fabric=fabric_name,
                    stains_count=len(enriched_stains),
                    routed_bin=decision["bin_id"],
                    garment_weight_kg=bin_load["added_weight_kg"]
                )

                latency_ms = int((time.time() - start_t) * 1000)

                st.session_state.last_analysis_result = {
                    "annotated_img": annotated_img,
                    "color_profile": color_profile,
                    "fabric": (fabric_name, fabric_conf),
                    "stains": enriched_stains,
                    "decision": decision,
                    "guardrail_safe": is_safe,
                    "guardrail_violations": guard_violations,
                    "grasp": grasp,
                    "latency_ms": latency_ms,
                    "bbox": target_bbox,
                    "bin_load": bin_load
                }

    with col_robot:
        st.markdown("<div class='nx-card-title'>🤖 Robotic Arm Telemetry & Bin Routing</div>", unsafe_allow_html=True)

        if st.session_state.last_analysis_result is not None:
            res = st.session_state.last_analysis_result
            dec = res["decision"]
            grasp = res["grasp"]
            col_p = res["color_profile"]

            # Key Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Fabric", res["fabric"][0], f"{res['fabric'][1]*100:.0f}%")
            m2.metric("Color", col_p["color_name"], f"Bleed: {col_p['bleed_risk']}")
            m3.metric("Stains", f"{len(res['stains'])} Found", f"{res['latency_ms']} ms")

            # Guardrail Status Banner
            if res["guardrail_safe"]:
                st.markdown("<div style='background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; border-radius: 6px; padding: 6px 12px; font-size: 0.75rem; color: #10B981; margin: 10px 0;'>🛡️ Safety Guardrails: Verified Safe (Zero Violations)</div>", unsafe_allow_html=True)
            else:
                for v in res["guardrail_violations"]:
                    st.error(f"⚠️ Guardrail Intercept: {v}")

            # Routing Destination Box
            st.markdown(f"""
            <div style="background: rgba(6, 182, 212, 0.08); border: 2px solid #06B6D4; border-radius: 10px; padding: 16px; margin: 12px 0;">
                <div style="font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; color: #06B6D4; text-transform: uppercase;">TARGET PHYSICAL SORTING BIN</div>
                <div style="font-size: 1.5rem; font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #FFF; margin: 4px 0;">{dec['bin_id']}</div>
                <div style="font-size: 0.9rem; font-weight: 600; color: #E0F2FE;">{dec['bin_name']}</div>
                <div style="font-size: 0.8rem; color: #9CA3AF; margin-top: 6px;"><b>Wash Recipe:</b> {dec['recipe']['temp']} | {dec['recipe']['cycle']}</div>
            </div>
            """, unsafe_allow_html=True)

            # Specific Stain Chemical Prescriptions Card
            if res["stains"]:
                st.markdown("<div class='nx-card-title' style='margin-top: 15px;'>🧪 Chemical Spot-Treatment Formulations</div>", unsafe_allow_html=True)
                for s_idx, stn in enumerate(res["stains"]):
                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.02); border-left: 3px solid #F59E0B; padding: 8px 12px; margin-bottom: 8px; border-radius: 4px;">
                        <div style="font-weight: 600; font-size: 0.85rem; color: #F59E0B;">Stain #{s_idx+1}: {stn['stain_name']} (Conf: {stn['classifier_confidence']*100:.0f}%)</div>
                        <div style="font-size: 0.78rem; color: #D1D5DB; margin-top: 2px;"><b>Agent:</b> {stn['chemical_agent']}</div>
                        <div style="font-size: 0.75rem; color: #9CA3AF;"><b>Max Safe Temp:</b> {stn['max_safe_temp_c']}°C | <b>Dwell:</b> {stn['min_dwell_min']} min | <b>Action:</b> {stn['mechanical_action']}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Robotic Motion Trajectory Details
            coords = grasp["pick_coords_mm"]
            drop = dec["robot_target_coords"]
            st.markdown(f"""
            <div class="nx-card">
                <div class="nx-card-title">Manipulator Trajectory Parameters</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #D1D5DB; line-height: 1.8;">
                    <b>Pick Location:</b> X: {coords['x']} mm | Y: {coords['y']} mm | Z: {coords['z']} mm<br>
                    <b>Target Bin Drop:</b> X: {drop['x']} mm | Y: {drop['y']} mm | Z: {drop['z']} mm<br>
                    <b>Grip Suction Force:</b> {grasp['grip_force_n']} N | <b>Speed:</b> {grasp['approach_speed_pct']}%
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("🚀 Execute Robotic Pick & Place", use_container_width=True):
                    with st.spinner(f"Dispatched Arm to {dec['bin_id']}..."):
                        packet = robot_controller.dispatch_pick_and_place(
                            bbox=res["bbox"],
                            bin_id=dec["bin_id"],
                            fabric=res["fabric"][0],
                            item_label=f"{col_p['color_name']} {res['fabric'][0]}"
                        )
                        st.success(f"Executed Cycle #{packet['cycle_id']} in {packet['cycle_duration_ms']}ms!")
                        st.rerun()

            with col_d2:
                if st.button("💾 Save Item to Batch Log", use_container_width=True):
                    db = next(get_db())
                    item = WardrobeItem(
                        color=col_p["color_name"],
                        fabric=res["fabric"][0],
                        stain_status=str(len(res["stains"])),
                        wash_instructions=dec["instructions"],
                        user_id=st.session_state.operator_id
                    )
                    db.add(item)
                    db.commit()
                    st.success("Logged into Batch Audit Table!")

        else:
            st.info("Awaiting scan. Trigger an inspection snapshot from the live camera on the left.")

# =============================================================================
# 2. CONVEYOR BATCH SORTER (MULTI-ITEM DETECTION & BLEED CHECK)
# =============================================================================
elif app_mode == "Conveyor Batch Sorter":
    st.markdown("<div class='nx-card-title'>📦 Multi-Garment Conveyor Inspection Zone</div>", unsafe_allow_html=True)
    st.write("Detects multiple clothing items on the conveyor simultaneously, calculates individual robotic pick coordinates, and runs color bleed cross-contamination checks.")

    uploaded_batch = st.file_uploader("Upload Conveyor Belt Batch Image", type=["jpg", "jpeg", "png"])
    
    if uploaded_batch:
        raw_b = uploaded_batch.read()
        is_v, san_img, _ = SecurityValidator.validate_and_sanitize_image(raw_b)
        img_np = san_img if is_v else np.array(Image.open(io.BytesIO(raw_b)).convert('RGB'))
        st.image(img_np, use_column_width=True, caption="Conveyor Belt Workzone")

        with st.spinner("Extracting individual garments and computing robotic grasp coordinates..."):
            items = clothing_detector.extract_garments_with_metadata(img_np)
            st.success(f"Detected {len(items)} individual garments on the conveyor belt.")

            batch_results = []
            for it in items:
                crop = it["crop"]
                raw_stains, _ = stain_detector.detect_stains(crop)
                enriched_stains = stain_classifier.enrich_detected_stains(crop, raw_stains)
                fabric, conf = fabric_classifier.predict_fabric(crop)
                col_p = color_classifier.analyze_color_profile(crop)
                dec = decision_engine.decide_industrial_routing(
                    color=col_p["category"],
                    fabric=fabric,
                    stains=enriched_stains,
                    color_name=col_p["color_name"],
                    bleed_risk=col_p["bleed_risk"]
                )
                grasp = robot_controller.compute_grasp_parameters(it["bbox"], fabric)

                batch_results.append({
                    "crop": crop,
                    "bbox": it["bbox"],
                    "color_name": col_p["color_name"],
                    "color": col_p["category"],
                    "bleed_risk": col_p["bleed_risk"],
                    "fabric": fabric,
                    "stains": len(enriched_stains),
                    "stain_details": enriched_stains,
                    "bin": dec["bin_id"],
                    "pick_coords": grasp["pick_coords_mm"]
                })

            safety_report = clothing_detector.check_mixed_safety(batch_results)
            st.markdown(f"### Batch Safety Audit\n{safety_report}")

            st.markdown("### Item-by-Item Pick & Routing Queue")
            for idx, r in enumerate(batch_results):
                with st.expander(f"Item #{idx+1}: {r['color_name']} {r['fabric']} → Route to {r['bin']}"):
                    col_i1, col_i2 = st.columns([1, 2])
                    with col_i1:
                        st.image(r["crop"], width=180)
                    with col_i2:
                        st.write(f"**Bleed Risk:** {r['bleed_risk']} | **Stains:** {r['stains']}")
                        if r["stain_details"]:
                            st.write(f"**Stain Prescription:** {r['stain_details'][0]['chemical_agent']}")
                        st.write(f"**Robot Pick Coordinates:** X={r['pick_coords']['x']} mm, Y={r['pick_coords']['y']} mm, Z={r['pick_coords']['z']} mm")
                        if st.button(f"Pick & Route Item #{idx+1}", key=f"btn_pick_{idx}"):
                            robot_controller.dispatch_pick_and_place(r["bbox"], r["bin"], r["fabric"])
                            st.success(f"Item #{idx+1} routed to {r['bin']}!")

# =============================================================================
# 3. CARE TAG OPTICAL SCANNER (ISO 3758 SYMBOL CLASSIFIER + OCR)
# =============================================================================
elif app_mode == "Care Tag Optical Scanner (ISO 3758)":
    st.markdown("<div class='nx-card-title'>🏷️ Macro Optical Care Label Scanner (CAM_02 Dedicated Tag Optics)</div>", unsafe_allow_html=True)
    st.write("Extracts manufacturer washing constraints and classifies universal ISO 3758 care symbol icons (Washtub, Triangle, Square, Iron, Circle) even when text is faded.")

    tag_source = st.radio("Optics Input", ["Macro Optical Camera (CAM_02)", "Upload Macro Tag Image"], horizontal=True)

    tag_np = None
    if tag_source == "Macro Optical Camera (CAM_02)":
        tag_np = multi_camera.capture_macro_tag_frame()
        st.image(tag_np, width=420, caption="Live Feed: CAM_02 Macro Tag Optics")
    else:
        tag_upload = st.file_uploader("Upload Macro Care Label Photo", type=["jpg", "jpeg", "png"])
        if tag_upload:
            raw_b = tag_upload.read()
            is_v, san_img, _ = SecurityValidator.validate_and_sanitize_image(raw_b)
            tag_np = san_img if is_v else np.array(Image.open(io.BytesIO(raw_b)).convert('RGB'))
            st.image(tag_np, width=420, caption="Uploaded Care Label Macro Image")

    if tag_np is not None:
        if st.button("🔍 Execute ISO 3758 Symbol Vision Analysis & OCR"):
            with st.spinner("Analyzing geometric symbols and parsing operational restrictions..."):
                symbol_results = care_symbol_classifier.classify_tag_symbols(tag_np)
                structured_ocr = ocr_reader.extract_structured_tag(tag_np)

                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.markdown("#### Detected ISO 3758 Symbols")
                    if symbol_results["symbols"]:
                        for sym in symbol_results["symbols"]:
                            st.markdown(f"• **{sym['symbol']}** ({sym['category']}) · Confidence: {sym['confidence']*100:.0f}%")
                    else:
                        st.info("No distinct isolated geometric icons detected. Falling back to OCR text.")

                    st.markdown("#### Safety Flags")
                    st.write(f"Dry Clean Only: {'🔴 YES' if (symbol_results['safety_flags']['dry_clean_only'] or structured_ocr['is_dry_clean_only']) else '🟢 NO'}")
                    st.write(f"Bleach Prohibited: {'🔴 YES' if (symbol_results['safety_flags']['bleach_forbidden'] or structured_ocr['bleach_forbidden']) else '🟢 NO'}")

                with col_s2:
                    st.markdown("#### OCR Extracted Text & Keywords")
                    st.code(structured_ocr["raw_text"] if structured_ocr["raw_text"] else "[Text analysis complete]")
                    if symbol_results["restrictions"]:
                        st.markdown("#### Active Operational Restrictions")
                        for rst in symbol_results["restrictions"]:
                            st.markdown(f"⚠️ {rst}")

# =============================================================================
# 4. SMART FACTORY LOAD BALANCER & SUSTAINABILITY DASHBOARD
# =============================================================================
elif app_mode == "Smart Factory Load Balancer & Sustainability":
    st.markdown("<div class='nx-card-title'>⚖️ Physical Bin Load Balancing & Automated Washer Dispatch</div>", unsafe_allow_html=True)
    st.write("Monitors cumulative garment weights and volumes per sorting bin. When a bin reaches target washer batch size (e.g., 15 kg), it alerts operators for washing machine loading.")

    capacity_data = load_balancer.get_workcell_capacity_summary()

    m1, m2, m3 = st.columns(3)
    m1.metric("Facility Processed Garments", f"{capacity_data['total_facility_garments']}")
    m2.metric("Cumulative Load Weight", f"{capacity_data['total_facility_weight_kg']} kg")
    m3.metric("Bins Ready for Washer", f"{len(capacity_data['bins_ready_for_washing'])}")

    st.markdown("### Sorting Bins Live Fill Telemetry")
    for bid, binfo in capacity_data["bins"].items():
        fill_pct = min(100.0, (binfo["current_weight_kg"] / binfo["max_capacity_kg"]) * 100.0)
        col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
        with col_b1:
            st.markdown(f"**{bid}**: {binfo['name']} ({binfo['current_weight_kg']} kg / {binfo['max_capacity_kg']} kg)")
            st.progress(fill_pct / 100.0)
        with col_b2:
            st.write(f"Status: **{binfo['status']}**")
        with col_b3:
            if st.button(f"Unload {bid} to Washer", key=f"unload_{bid}"):
                unl = load_balancer.unload_bin_to_washer(bid)
                st.success(f"{bid} cleared! Dispatched {unl['unloaded_weight_kg']} kg to washer.")
                st.rerun()

    st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 30px 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='nx-card-title'>🌱 Sustainability & Environmental ROI Telemetry</div>", unsafe_allow_html=True)

    sust = sustainability_engine.get_summary()
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("💧 Water Conserved", f"{sust['water_saved_liters']} L", "Avoided re-washes")
    sc2.metric("⚡ Energy Conserved", f"{sust['energy_saved_kwh']} kWh", "Cold-wash optimization")
    sc3.metric("🌍 Carbon Offset", f"{sust['carbon_offset_kg_co2']} kg CO₂e", "Grid reduction")
    sc4.metric("💵 Capital Protected", f"${sust['financial_capital_saved_usd']}", "Prevented ruined clothes")

# =============================================================================
# 5. FACTORY BATCH TELEMETRY & WARDROBE
# =============================================================================
elif app_mode == "Factory Batch Telemetry & Wardrobe":
    st.markdown("<div class='nx-card-title'>📊 Batch Production Telemetry & Audit Logs</div>", unsafe_allow_html=True)

    db = next(get_db())
    items = db.query(WardrobeItem).order_by(WardrobeItem.date_added.desc()).all()

    st.write(f"Total garments processed and logged in facility database: **{len(items)}**")

    if items:
        records = []
        for it in items:
            records.append({
                "ID": it.id,
                "Color": it.color,
                "Fabric": it.fabric,
                "Stains": it.stain_status,
                "Routing & Wash Parameters": it.wash_instructions,
                "Timestamp": it.date_added.strftime("%Y-%m-%d %H:%M")
            })
        st.dataframe(records, use_container_width=True)

        if st.button("📄 Export Complete Workcell Batch PDF Guide"):
            last_item = items[0]
            pdf_path = generate_care_pdf(last_item.color, last_item.fabric, last_item.stain_status, last_item.wash_instructions)
            with open(pdf_path, "rb") as f:
                st.download_button("Download Generated PDF", f, file_name="NexusCareGuide.pdf", mime="application/pdf")
    else:
        st.info("No batches logged yet. Inspect an item in the workcell and click 'Save to Batch Log'.")

# =============================================================================
# 6. SYSTEM DIAGNOSTICS & EVALS BENCHMARK
# =============================================================================
elif app_mode == "System Diagnostics & Evals Benchmark":
    st.markdown("<div class='nx-card-title'>⚙️ Automated Workcell Evals & Benchmark Scorecard</div>", unsafe_allow_html=True)
    st.write("Executes comprehensive verification across colorimetry, fabric spatial frequency, stain chemistry, zero-tolerance safety guardrails, and sub-30ms edge latency.")

    if st.button("🧪 Run Automated Workcell Benchmark Suite"):
        with st.spinner("Executing multi-target verification and adversarial stress-testing..."):
            scorecard = benchmark_harness.run_full_benchmark_suite()
            st.success(f"Benchmark Suite Status: {scorecard['overall_status']} (Execution: {scorecard['execution_duration_ms']}ms)")
            st.json(scorecard)

    st.markdown("#### Hardware Diagnostics & Calibration Matrices")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Optics Specs")
        st.json(multi_camera.get_system_diagnostics())
    with c2:
        st.markdown("##### Robotic Arm Calibration")
        st.json({
            "scale_x": f"{robot_controller.scale_x} mm/pixel",
            "scale_y": f"{robot_controller.scale_y} mm/pixel",
            "conveyor_height_z": f"{robot_controller.conveyor_z} mm",
            "e_stop_status": robot_controller.emergency_stop
        })
