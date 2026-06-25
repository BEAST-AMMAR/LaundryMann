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
from src.models.ocr_reader import OCRReader
from src.models.clothing_detector import ClothingDetector
from src.utils.pdf_generator import generate_care_pdf
from src.database import get_db, WardrobeItem, User
import extra_streamlit_components as stx# =============================================================================
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
def get_theme_css():
    return """<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-primary: #08080C;
        --bg-sidebar: #0C0C12;
        --bg-card: rgba(255, 255, 255, 0.02);
        --bg-card-hover: rgba(255, 255, 255, 0.04);
        --bg-input: rgba(255, 255, 255, 0.03);
        --border: rgba(255, 255, 255, 0.08);
        --border-hover: rgba(255, 255, 255, 0.15);
        --border-glow: rgba(139, 92, 246, 0.4);
        --text-primary: #F3F4F6;
        --text-secondary: #9CA3AF;
        --text-muted: #6B7280;
        --accent: #8B5CF6;
        --accent-glow: rgba(139, 92, 246, 0.25);
        --cyan: #06B6D4;
        --cyan-glow: rgba(6, 182, 212, 0.25);
        --shadow-inset: inset 0 1px 1px rgba(255, 255, 255, 0.05);
        --shadow-drop: 0 8px 32px rgba(0, 0, 0, 0.6);
        --transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* Aggressive Streamlit Cleanup */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Background with subtle grain texture emulation */
    html, body, .stApp {
        font-family: 'Inter', -apple-system, sans-serif !important;
        background-color: var(--bg-primary) !important;
        background-image: radial-gradient(circle at 50% 0%, rgba(139,92,246,0.06) 0%, transparent 50%),
                          radial-gradient(circle at 80% 100%, rgba(6,182,212,0.04) 0%, transparent 40%);
        color: var(--text-primary);
        letter-spacing: -0.015em;
    }

    /* Sidebar: Deep Obsidian */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border) !important;
        padding-top: 2rem;
    }
    section[data-testid="stSidebar"] .stMarkdown h1, h2, h3, p { color: var(--text-primary) !important; }
    section[data-testid="stSidebar"] hr { border-color: var(--border); margin: 2rem 0; }
    
    /* Navigation Highlight */
    .stRadio > div > label {
        background: transparent;
        padding: 8px 12px;
        border-radius: 6px;
        transition: var(--transition);
        border: 1px solid transparent;
    }
    .stRadio > div > label:hover {
        background: var(--bg-card-hover);
        border-color: var(--border);
    }

    /* Cards: Translucent, Inset Shadow */
    .nx-card {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 24px;
        box-shadow: var(--shadow-drop), var(--shadow-inset);
        transition: var(--transition);
    }
    .nx-card:hover {
        border-color: var(--border-hover);
        background: var(--bg-card-hover);
    }
    .nx-card-title { 
        font-size: 0.75rem; font-weight: 600; color: var(--text-muted); 
        text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 16px; display: block;
    }

    /* Auth Form Styling */
    .auth-container {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 48px 40px;
        box-shadow: var(--shadow-drop), var(--shadow-inset);
        margin: 20px auto;
        max-width: 400px;
        position: relative;
        overflow: hidden;
    }
    /* Auth top glowing accent line */
    .auth-container::before {
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent), var(--cyan), transparent);
        opacity: 0.8;
    }
    
    .hero-title {
        font-weight: 800; font-size: 2.5rem; letter-spacing: -0.05em; line-height: 1.1;
        background: linear-gradient(180deg, #FFFFFF 0%, #A1A1AA 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 8px; text-shadow: 0 2px 20px rgba(255,255,255,0.05);
    }
    .hero-badge {
        display: inline-block; background: rgba(139,92,246,0.1); color: var(--accent);
        font-size: 0.7rem; font-weight: 700; padding: 4px 10px; border-radius: 999px;
        border: 1px solid var(--border-glow); margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.1em;
    }
    
    /* Streamlit Overrides */
    /* Buttons: Beautiful sleek violet actions */
    .stButton > button {
        background: rgba(255,255,255,0.03) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        padding: 10px 16px !important;
        transition: var(--transition) !important;
        box-shadow: var(--shadow-inset);
        width: 100%;
    }
    .stButton > button:hover {
        background: rgba(139,92,246,0.15) !important;
        border-color: var(--accent) !important;
        box-shadow: 0 0 16px var(--accent-glow), var(--shadow-inset) !important;
        color: #fff !important;
    }
    
    /* Inputs */
    .stTextInput input {
        background: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        padding: 12px 14px !important;
        font-size: 0.95rem;
        transition: var(--transition);
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
    }
    .stTextInput input:focus { 
        border-color: var(--accent) !important; 
        box-shadow: 0 0 0 1px var(--accent), inset 0 2px 4px rgba(0,0,0,0.2) !important; 
    }
    
    /* Tabs Overrides */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent; border-bottom: 1px solid var(--border); gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important; color: var(--text-secondary) !important;
        font-size: 0.9rem; font-weight: 500; border: none !important; padding-bottom: 12px !important;
        transition: var(--transition);
    }
    .stTabs [aria-selected="true"] {
        color: var(--text-primary) !important; border-bottom: 2px solid var(--accent) !important;
        text-shadow: 0 0 12px var(--accent-glow);
    }
    
    /* Metric Boxes */
    div[data-testid="metric-container"] {
        background: var(--bg-card) !important; border: 1px solid var(--border) !important;
        border-radius: 12px !important; padding: 24px !important;
        box-shadow: var(--shadow-drop), var(--shadow-inset);
        transition: var(--transition);
    }
    div[data-testid="metric-container"]:hover { border-color: var(--accent) !important; transform: translateY(-1px); }
    div[data-testid="metric-container"] label { color: var(--text-secondary) !important; font-size: 0.75rem !important; font-weight: 500 !important; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: var(--text-primary) !important; font-family: 'JetBrains Mono', monospace !important; font-weight: 600 !important; font-size: 1.8rem !important; letter-spacing: -0.02em;}
    div[data-testid="metric-container"] [data-testid="stMetricDelta"] { color: var(--cyan) !important; font-family: 'JetBrains Mono', monospace !important; text-shadow: 0 0 8px var(--cyan-glow);}

    /* Live Dot */
    .nx-live-dot { display: inline-flex; align-items: center; gap: 6px; font-size: 0.75rem; font-weight: 600; color: var(--cyan); }
    .nx-live-dot::before { content: ''; width: 6px; height: 6px; background: var(--cyan); border-radius: 50%; box-shadow: 0 0 8px var(--cyan-glow); }
    
    /* File Uploader - Dropzone */
    div[data-testid="stFileUploader"] { 
        background: var(--bg-input) !important; 
        border: 1px dashed var(--border) !important; 
        border-radius: 12px !important; 
        padding: 40px !important; 
        text-align: center;
        transition: var(--transition);
    }
    div[data-testid="stFileUploader"]:hover { 
        border-color: var(--accent) !important; 
        background: rgba(139,92,246,0.03) !important;
    }
    </style>"""
st.markdown(get_theme_css(), unsafe_allow_html=True)

# =============================================================================
# MODEL INITIALIZATION
# =============================================================================
@st.cache_resource
def load_models():
    stain_detector = StainDetector()
    fabric_classifier = FabricClassifier()
    color_classifier = ColorClassifier()
    decision_engine = LaundryDecisionEngine()
    ocr_reader = OCRReader()
    clothing_detector = ClothingDetector()
    return stain_detector, fabric_classifier, color_classifier, decision_engine, ocr_reader, clothing_detector

stain_detector, fabric_classifier, color_classifier, decision_engine, ocr_reader, clothing_detector = load_models()

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
# AUTHENTICATION FLOW
# =============================================================================
from src.database import verify_password, get_password_hash
db = next(get_db())

@st.cache_resource(experimental_allow_widgets=True)
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None

# Auto-login via persistent cookie
auth_cookie = cookie_manager.get(cookie="nexus_auth")
if auth_cookie and not st.session_state.logged_in:
    user = db.query(User).filter(User.username == auth_cookie).first()
    if user:
        st.session_state.logged_in = True
        st.session_state.user_id = user.id
        st.session_state.username = user.username

if not st.session_state.logged_in:
    st.markdown('<div style="text-align: center; margin-top: 12vh;">', unsafe_allow_html=True)
    st.markdown('<span class="hero-badge">⬡ NEXUS SECURE</span>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Welcome to Nexus</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--text-secondary); font-size: 1.1rem;">Authenticate to access your Digital Wardrobe.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])
        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Authenticate", use_container_width=True):
                user = db.query(User).filter(User.username == username).first()
                if user and verify_password(password, user.password_hash):
                    st.session_state.logged_in = True
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    # Set persistent cookie for 30 days
                    cookie_manager.set("nexus_auth", user.username, max_age=30*24*60*60)
                    time.sleep(0.5) # Wait for cookie to propagate to browser
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials.")
        with tab2:
            new_user = st.text_input("Choose Username", key="reg_user")
            new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
            if st.button("Register Account", use_container_width=True):
                if db.query(User).filter(User.username == new_user).first():
                    st.error("Username taken.")
                else:
                    u = User(username=new_user, password_hash=get_password_hash(new_pass))
                    db.add(u)
                    db.commit()
                    st.success("Registered successfully! Please login.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# =============================================================================
# SIDEBAR — SENSOR CONTROLS
# =============================================================================
with st.sidebar:
    st.markdown("#### ⬡ NEXUS CONTROLS")
    st.markdown(f'<div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 12px;">Logged in as: <b style="color: var(--text-primary)">{st.session_state.username}</b></div>', unsafe_allow_html=True)
    if st.button("Logout"):
        cookie_manager.delete("nexus_auth")
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.experimental_rerun()
        
    st.markdown('<hr class="nx-divider">', unsafe_allow_html=True)

    st.markdown('<hr class="nx-divider">', unsafe_allow_html=True)

    app_mode = st.radio("NAVIGATION", ["Scan Single Garment", "Basket Scan (Multi-Item)", "My Digital Wardrobe"])

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
if app_mode == "Scan Single Garment":
    st.markdown('<p class="nx-section-label">Initialize Scan</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader("Drop a garment image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    with col2:
        tag_file = st.file_uploader("Optional: Care Label Photo (for OCR)", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        
    if uploaded_file is not None:
        st.markdown('<hr class="nx-divider">', unsafe_allow_html=True)
    
        image = Image.open(uploaded_file)
        img_array = np.array(image.convert('RGB'))
        
        # OCR Processing
        ocr_instructions = []
        ocr_text = ""
        if tag_file:
            tag_img = np.array(Image.open(tag_file).convert('RGB'))
            ocr_text = ocr_reader.read_care_label(tag_img)
            ocr_instructions = ocr_reader.parse_care_instructions(ocr_text)
        
        # Run inference
        with st.spinner("Analyzing multispectral data..."):
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
            
            if ocr_instructions:
                instructions += "\\n\\n[OCR Override]: " + ", ".join(ocr_instructions)
                
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
            st.image(annotated_img, use_column_width=True)
    
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
    
            # Routing Decision
            st.markdown(f"""
            <div class="nx-routing">
                <div class="nx-routing-label">Robotic Routing Decision</div>
                <div class="nx-routing-value">{routing_bin}</div>
                <div class="nx-routing-instructions">{instructions}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action Buttons
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                # Save to DB
                if st.button("Save to Wardrobe"):
                    db = next(get_db())
                    item = WardrobeItem(color=color_label, fabric=fabric_label, stain_status=str(len(stains)), wash_instructions=instructions, user_id=st.session_state.user_id)
                    db.add(item)
                    db.commit()
                    st.success("Saved successfully!")
                    
            with action_col2:
                if st.button("Generate PDF Care Guide"):
                    pdf_path = generate_care_pdf(color_label, fabric_label, str(len(stains)), instructions)
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(label="Download PDF", data=pdf_file, file_name="CareGuide.pdf", mime="application/pdf")
    
    else:
        st.markdown("""
        <div style="text-align: center; padding: 80px 20px;">
            <div style="font-size: 3.5rem; margin-bottom: 16px; opacity: 0.3;">⬡</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px;">
                No Garment Scanned
            </div>
        </div>
        """, unsafe_allow_html=True)

elif app_mode == "Basket Scan (Multi-Item)":
    st.markdown('<p class="nx-section-label">Multi-Item Sorting</p>', unsafe_allow_html=True)
    basket_file = st.file_uploader("Upload an image of your laundry basket", type=["jpg", "jpeg", "png"])
    
    if basket_file:
        image = Image.open(basket_file)
        img_array = np.array(image.convert('RGB'))
        st.image(image, use_column_width=True)
        
        with st.spinner("Isolating garments..."):
            crops = clothing_detector.extract_garments(img_array)
            st.write(f"Detected {len(crops)} distinct items in the basket.")
            
            results = []
            for crop in crops:
                stains, _ = stain_detector.detect_stains(crop)
                fabric_label, _ = fabric_classifier.predict_fabric(crop)
                color_label, _ = color_classifier.predict_color(crop)
                results.append({"color": color_label, "fabric": fabric_label, "stains": len(stains)})
                
            report = clothing_detector.check_mixed_safety(results)
            st.info(report)
            st.json(results)

elif app_mode == "My Digital Wardrobe":
    st.markdown(f"<p class='nx-section-label'>{st.session_state.username}'s Digital Wardrobe</p>", unsafe_allow_html=True)
    
    db = next(get_db())
    items = db.query(WardrobeItem).filter(WardrobeItem.user_id == st.session_state.user_id).order_by(WardrobeItem.date_added.desc()).all()
    
    if not items:
        st.write("Your wardrobe is empty. Scan an item and save it!")
    else:
        for item in items:
            with st.expander(f"{item.color} {item.fabric} - Added {item.date_added.strftime('%Y-%m-%d')}"):
                st.write(f"**Stains:** {item.stain_status}")
                st.write(f"**Instructions:** {item.wash_instructions}")
