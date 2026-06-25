import streamlit as st
import cv2
import numpy as np
from PIL import Image
import os
import io
import time

from src.models.stain_detector import StainDetector
from src.models.fabric_classifier import FabricClassifier
from src.models.color_classifier import ColorClassifier
from src.core.decision_engine import LaundryDecisionEngine

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="NEXUS · Robotic Sorter AI",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# PREMIUM DARK CHARCOAL THEME — FULL CSS REDESIGN
# =============================================================================
THEME_CSS = """
<style>
    /* ── Google Fonts ─────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ── CSS Custom Properties ────────────────────────── */
    :root {
        --bg-primary:    #101114;
        --bg-secondary:  #18191d;
        --bg-card:       #1e1f24;
        --bg-card-hover: #25262c;
        --bg-elevated:   #2a2b32;
        --border-subtle: rgba(255,255,255,0.06);
        --border-active: rgba(255,255,255,0.12);
        --text-primary:  #f0f0f2;
        --text-secondary:#9a9ba1;
        --text-muted:    #62636a;
        --accent:        #6ee7b7;
        --accent-dim:    rgba(110,231,183,0.12);
        --accent-glow:   rgba(110,231,183,0.25);
        --danger:        #f87171;
        --danger-dim:    rgba(248,113,113,0.12);
        --info:          #93c5fd;
        --info-dim:      rgba(147,197,253,0.10);
        --warning:       #fbbf24;
        --warning-dim:   rgba(251,191,36,0.12);
        --radius-sm:     8px;
        --radius-md:     12px;
        --radius-lg:     16px;
        --radius-xl:     20px;
        --shadow:        0 1px 3px rgba(0,0,0,0.4), 0 4px 20px rgba(0,0,0,0.3);
        --shadow-lg:     0 8px 40px rgba(0,0,0,0.5);
        --transition:    all 0.25s cubic-bezier(0.4,0,0.2,1);
    }

    /* ── Global Reset ─────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: var(--bg-primary) !important;
        color: var(--text-primary);
    }

    /* Streamlit main container */
    .stApp {
        background-color: var(--bg-primary) !important;
    }
    
    header[data-testid="stHeader"] {
        background-color: var(--bg-primary) !important;
        border-bottom: 1px solid var(--border-subtle);
    }

    /* ── Sidebar ──────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--text-primary) !important;
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    section[data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-secondary) !important;
        font-size: 0.85rem;
        line-height: 1.6;
    }

    /* ── Checkbox Styling ─────────────────────────────── */
    section[data-testid="stSidebar"] .stCheckbox label {
        color: var(--text-primary) !important;
        font-weight: 500;
        font-size: 0.9rem;
    }

    /* ── Headings ─────────────────────────────────────── */
    h1, h2, h3 { color: var(--text-primary) !important; letter-spacing: -0.03em; }

    /* ── Hero Title ───────────────────────────────────── */
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        font-size: 2.8rem;
        letter-spacing: -0.04em;
        line-height: 1.1;
        background: linear-gradient(135deg, #f0f0f2 0%, #9a9ba1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: var(--accent-dim);
        color: var(--accent);
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 5px 12px;
        border-radius: 100px;
        border: 1px solid rgba(110,231,183,0.15);
        margin-bottom: 6px;
    }

    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 400;
        letter-spacing: -0.01em;
        margin-bottom: 2rem;
    }

    /* ── Divider ──────────────────────────────────────── */
    .nx-divider {
        height: 1px;
        background: var(--border-subtle);
        margin: 1.5rem 0;
        border: none;
    }

    /* ── Cards ────────────────────────────────────────── */
    .nx-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 24px;
        box-shadow: var(--shadow);
        transition: var(--transition);
    }
    .nx-card:hover {
        border-color: var(--border-active);
        background: var(--bg-card-hover);
    }

    .nx-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
    }

    .nx-card-title {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-secondary);
    }

    .nx-live-dot {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--accent);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .nx-live-dot::before {
        content: '';
        width: 6px;
        height: 6px;
        background: var(--accent);
        border-radius: 50%;
        box-shadow: 0 0 8px var(--accent-glow);
        animation: pulse-dot 2s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }

    /* ── Metric Tiles ─────────────────────────────────── */
    .nx-metric {
        background: var(--bg-secondary);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 18px 16px;
        text-align: center;
        transition: var(--transition);
    }
    .nx-metric:hover {
        border-color: var(--border-active);
        transform: translateY(-1px);
    }
    .nx-metric-label {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        margin-bottom: 6px;
    }
    .nx-metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.2;
    }
    .nx-metric-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--accent);
        margin-top: 4px;
    }

    /* ── Routing Decision Banner ──────────────────────── */
    .nx-routing {
        background: var(--bg-secondary);
        border: 1px solid var(--accent);
        border-left: 4px solid var(--accent);
        border-radius: var(--radius-md);
        padding: 20px 24px;
        margin: 16px 0;
    }
    .nx-routing-label {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--accent);
        margin-bottom: 6px;
    }
    .nx-routing-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .nx-routing-instructions {
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-top: 8px;
        line-height: 1.5;
    }

    /* ── Wash Cycle Card ──────────────────────────────── */
    .nx-wash-card {
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 28px;
        text-align: center;
        margin-top: 12px;
    }
    .nx-wash-cycle {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--accent);
        margin-bottom: 4px;
    }
    .nx-wash-temp {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.8rem;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1;
        margin: 8px 0;
    }
    .nx-wash-detergent {
        font-size: 0.85rem;
        color: var(--text-secondary);
        font-weight: 500;
    }

    /* ── Alert Banner ─────────────────────────────────── */
    .nx-alert {
        background: var(--danger-dim);
        border: 1px solid rgba(248,113,113,0.25);
        border-left: 4px solid var(--danger);
        border-radius: var(--radius-md);
        padding: 14px 18px;
        color: var(--danger);
        font-weight: 600;
        font-size: 0.88rem;
        margin: 12px 0;
        animation: alert-flash 3s ease-in-out infinite;
    }
    @keyframes alert-flash {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.75; }
    }

    /* ── Upload Area ──────────────────────────────────── */
    .nx-upload-zone {
        background: var(--bg-card);
        border: 2px dashed var(--border-active);
        border-radius: var(--radius-lg);
        padding: 28px;
        text-align: center;
        transition: var(--transition);
    }
    .nx-upload-zone:hover {
        border-color: var(--accent);
        background: var(--bg-card-hover);
    }

    .nx-upload-icon {
        font-size: 2rem;
        margin-bottom: 8px;
    }
    .nx-upload-text {
        color: var(--text-secondary);
        font-size: 0.88rem;
    }
    .nx-upload-text strong {
        color: var(--accent);
    }

    /* ── Streamlit Overrides ──────────────────────────── */
    /* File uploader */
    div[data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 2px dashed var(--border-active) !important;
        border-radius: var(--radius-lg) !important;
        padding: 16px !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: var(--accent) !important;
    }

    /* Metric containers */
    div[data-testid="metric-container"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        padding: 16px !important;
        text-align: center !important;
    }
    div[data-testid="metric-container"] label {
        color: var(--text-muted) !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 700 !important;
    }
    div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
        color: var(--accent) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Expander */
    details[data-testid="stExpander"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
    }
    details[data-testid="stExpander"] summary {
        color: var(--text-secondary) !important;
        font-weight: 500;
    }

    /* Spinner */
    .stSpinner > div {
        border-color: var(--accent) transparent transparent transparent !important;
    }

    /* Buttons */
    .stButton > button {
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-active) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 8px 20px !important;
        transition: var(--transition) !important;
    }
    .stButton > button:hover {
        background: var(--accent-dim) !important;
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        transform: translateY(-1px);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background: var(--bg-secondary);
        border-radius: var(--radius-md);
        padding: 4px;
        border: 1px solid var(--border-subtle);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm);
        color: var(--text-secondary) !important;
        font-weight: 500;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
    }

    /* Info/Warning/Error/Success boxes */
    div[data-testid="stAlert"] {
        border-radius: var(--radius-md) !important;
        font-size: 0.88rem;
    }

    /* Images */
    img {
        border-radius: var(--radius-md) !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--bg-elevated); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

    /* Section label */
    .nx-section-label {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-muted);
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border-subtle);
    }
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)

# =============================================================================
# MODEL INITIALIZATION
# =============================================================================
@st.cache_resource
def load_models():
    stain_detector = StainDetector()
    fabric_classifier = FabricClassifier()
    color_classifier = ColorClassifier()
    decision_engine = LaundryDecisionEngine()
    return stain_detector, fabric_classifier, color_classifier, decision_engine

stain_detector, fabric_classifier, color_classifier, decision_engine = load_models()

# Bin recommendation map
BIN_RECOMMENDATIONS = {
    "BIN_A": {"cycle": "Standard Wash", "temp": "40°C", "detergent": "Standard Powder Detergent"},
    "BIN_B": {"cycle": "Heavy Duty", "temp": "60°C", "detergent": "Heavy Enzyme Pre-Treat"},
    "BIN_C": {"cycle": "Cold Wash", "temp": "20°C", "detergent": "Color-Safe Liquid Detergent"},
    "BIN_D": {"cycle": "Stain Cycle", "temp": "30°C", "detergent": "Oxygen Booster + Pre-Treat Spray"},
    "BIN_E": {"cycle": "Delicate", "temp": "30°C", "detergent": "Mild Gentle Liquid"},
    "BIN_F": {"cycle": "Sanitize / Ozone", "temp": "Cold", "detergent": "Ozone Treatment Module"},
    "BIN_G": {"cycle": "Manual Inspection", "temp": "N/A", "detergent": "Manual Spot Cleaning Required"}
}

# =============================================================================
# SIDEBAR — SENSOR CONTROLS
# =============================================================================
with st.sidebar:
    st.markdown("#### ⬡ NEXUS CONTROLS")
    st.markdown('<hr class="nx-divider">', unsafe_allow_html=True)

    st.markdown('<p class="nx-section-label">Hardware Sensor Simulation</p>', unsafe_allow_html=True)
    st.markdown("Toggle simulated physical sensors to test Decision Engine override logic.")
    
    odor_detected = st.checkbox("💨  E-Nose · VOC / Odor Sensor")
    uv_fluorescence = st.checkbox("🔬  UV Multispectral · Invisible Stain")

    st.markdown('<hr class="nx-divider">', unsafe_allow_html=True)
    st.markdown('<p class="nx-section-label">System Status</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="nx-metric" style="margin-bottom: 8px;">
        <div class="nx-metric-label">Pipeline Status</div>
        <div class="nx-metric-value" style="color: var(--accent); font-size: 0.95rem;">● Online</div>
    </div>
    <div class="nx-metric" style="margin-bottom: 8px;">
        <div class="nx-metric-label">Loaded Models</div>
        <div class="nx-metric-value" style="font-size: 0.95rem;">3 / 3</div>
    </div>
    <div class="nx-metric">
        <div class="nx-metric-label">Inference Device</div>
        <div class="nx-metric-value" style="font-size: 0.95rem;">CPU</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="nx-divider">', unsafe_allow_html=True)
    st.caption("NEXUS Laundry AI v2.0 · © 2026")

# =============================================================================
# MAIN CONTENT — HERO
# =============================================================================
st.markdown('<span class="hero-badge">⬡ Commercial Grade AI</span>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">NEXUS Robotic Sorter</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Multispectral ensemble pipeline for autonomous garment classification & robotic routing</p>', unsafe_allow_html=True)

# =============================================================================
# UPLOAD SECTION
# =============================================================================
st.markdown('<p class="nx-section-label">Initialize Scan</p>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Drop a garment image to begin autonomous analysis",
    type=["jpg", "jpeg", "png"],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    st.markdown('<hr class="nx-divider">', unsafe_allow_html=True)

    image = Image.open(uploaded_file)
    img_array = np.array(image.convert('RGB'))
    
    # Run inference
    with st.spinner(""):
        start_time = time.time()
        stains, annotated_img = stain_detector.detect_stains(img_array)
        fabric_label, fabric_conf = fabric_classifier.predict_fabric(img_array)
        color_label, color_conf = color_classifier.predict_color(img_array)
        
        routing_bin, instructions = decision_engine.decide_routing(
            color=color_label,
            fabric=fabric_label,
            stains=stains,
            odor_detected=odor_detected,
            uv_fluorescence=uv_fluorescence
        )
        latency = int((time.time() - start_time) * 1000)

    rec = BIN_RECOMMENDATIONS.get(routing_bin, BIN_RECOMMENDATIONS["BIN_G"])

    # ── Results Grid ──────────────────────────────────
    col_vision, col_analysis = st.columns([1.2, 1], gap="large")

    with col_vision:
        st.markdown(f"""
        <div class="nx-card">
            <div class="nx-card-header">
                <span class="nx-card-title">📷 Vision Feed · YOLOv8</span>
                <span class="nx-live-dot">Live</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.image(annotated_img, use_container_width=True)

    with col_analysis:
        st.markdown(f"""
        <div class="nx-card">
            <div class="nx-card-header">
                <span class="nx-card-title">🧠 Ensemble Analysis</span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--text-muted);">{latency}ms</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Fabric", fabric_label, f"{fabric_conf*100:.1f}%")
        m2.metric("Color", color_label, f"{color_conf*100:.1f}%")
        m3.metric("Stains", f"{len(stains)}", "Detected")

        # Sensor Override Alert
        if odor_detected or uv_fluorescence:
            sensor_type = "E-Nose (VOC)" if odor_detected else "UV Multispectral"
            st.markdown(f"""
            <div class="nx-alert">
                ⚠ SENSOR OVERRIDE · {sensor_type} — All visual routing bypassed. Rerouted to specialized handling.
            </div>
            """, unsafe_allow_html=True)

        # Routing Decision
        st.markdown(f"""
        <div class="nx-routing">
            <div class="nx-routing-label">Robotic Routing Decision</div>
            <div class="nx-routing-value">{routing_bin}</div>
            <div class="nx-routing-instructions">{instructions}</div>
        </div>
        """, unsafe_allow_html=True)

        # Wash Cycle Recommendation
        st.markdown(f"""
        <div class="nx-wash-card">
            <div class="nx-wash-cycle">Recommended Cycle</div>
            <div class="nx-wash-temp">{rec['temp']}</div>
            <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">{rec['cycle']}</div>
            <div class="nx-wash-detergent">Pre-treat: {rec['detergent']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Raw Telemetry
        with st.expander("⌘  Raw JSON Telemetry"):
            st.json({
                "pipeline_latency_ms": latency,
                "models": {
                    "stain_detector": "YOLOv8n (runs/detect/stain_detector_v1)",
                    "color_classifier": "SimpleLaundryCNN (laundry_cnn.pth)",
                    "fabric_classifier": "YOLOv8n-cls (fallback)"
                },
                "inference": {
                    "color": {"prediction": color_label, "confidence": round(color_conf, 4)},
                    "fabric": {"prediction": fabric_label, "confidence": round(fabric_conf, 4)},
                    "stains_detected": len(stains),
                    "stain_details": stains
                },
                "sensors": {
                    "odor_override": odor_detected,
                    "uv_override": uv_fluorescence
                },
                "decision": {
                    "routing_bin": routing_bin,
                    "instructions": instructions,
                    "wash_cycle": rec
                }
            })
else:
    # Empty state
    st.markdown("""
    <div style="text-align: center; padding: 80px 20px;">
        <div style="font-size: 3.5rem; margin-bottom: 16px; opacity: 0.3;">⬡</div>
        <div style="font-size: 1.1rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px;">
            No Garment Scanned
        </div>
        <div style="font-size: 0.88rem; color: var(--text-muted); max-width: 400px; margin: 0 auto; line-height: 1.6;">
            Upload a garment image above to initialize the autonomous sorting pipeline. 
            The AI ensemble will analyze color, fabric texture, and stain presence concurrently.
        </div>
    </div>
    """, unsafe_allow_html=True)
