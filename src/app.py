import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pandas as pd
import plotly.express as px
import time
import os

# Import our custom modules
from src import auth
from src.models.stain_detector import StainDetector
from src.models.fabric_classifier import FabricClassifier
from src.models.color_classifier import ColorClassifier
from src.core.decision_engine import LaundryDecisionEngine

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Laundry Assistant AI",
    page_icon="🧺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("src/style.css")

# Initialize DB
auth.init_db()

# --- MODEL INITIALIZATION ---
@st.cache_resource
def load_models():
    stain_detector = StainDetector()
    fabric_classifier = FabricClassifier()
    color_classifier = ColorClassifier()
    decision_engine = LaundryDecisionEngine()
    return stain_detector, fabric_classifier, color_classifier, decision_engine

stain_detector, fabric_classifier, color_classifier, decision_engine = load_models()

def predict_laundry(image, odor_detected=False, uv_fluorescence=False):
    # Convert PIL Image to BGR/RGB numpy array for inference
    img_array = np.array(image.convert('RGB'))
    
    # Run inferences
    stains, annotated_img = stain_detector.detect_stains(img_array)
    fabric_label, fabric_conf = fabric_classifier.predict_fabric(img_array)
    color_label, color_conf = color_classifier.predict_color(img_array)
    
    # Run decision engine
    routing_bin, wash_instructions = decision_engine.decide_routing(
        color=color_label,
        fabric=fabric_label,
        stains=stains,
        odor_detected=odor_detected,
        uv_fluorescence=uv_fluorescence
    )
    
    # Map to cycle/temp recommendation
    BIN_RECOMMENDATIONS = {
        "BIN_A": {"cycle": "Standard", "temp": "40°C", "detergent": "Standard Detergent"},
        "BIN_B": {"cycle": "Heavy Duty", "temp": "60°C", "detergent": "Heavy Enzyme Pre-Treat"},
        "BIN_C": {"cycle": "Normal Cold", "temp": "20°C", "detergent": "Color-Safe Detergent"},
        "BIN_D": {"cycle": "Stain Cycle", "temp": "30°C", "detergent": "Oxygen Booster & Pre-Treat"},
        "BIN_E": {"cycle": "Delicate", "temp": "30°C", "detergent": "Mild/Gentle Liquid Detergent"},
        "BIN_F": {"cycle": "Sanitize", "temp": "Cold (Ozone)", "detergent": "Ozone Treatment"},
        "BIN_G": {"cycle": "Manual Spot Treatment", "temp": "N/A", "detergent": "Manual Inspection Required"}
    }
    
    rec = BIN_RECOMMENDATIONS.get(routing_bin, {"cycle": "Manual Spot Treatment", "temp": "N/A", "detergent": "Manual Inspection Required"})
    
    results = {
        "fabric": fabric_label,
        "fabric_conf": fabric_conf,
        "color": color_label,
        "color_conf": color_conf,
        "stains": stains,
        "stains_detected": len(stains),
        "annotated_img": annotated_img,
        "routing_bin": routing_bin,
        "wash_instructions": wash_instructions,
        "recommendation": rec
    }
    return results

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

# --- PAGES ---

def login_page():
    st.markdown("<h1 style='text-align: center; color: white;'>🧺 Laundry AI Login</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type='password', key="login_pass")
            if st.button("Login"):
                result = auth.login_user(username, password)
                if result:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.experimental_rerun()
                else:
                    st.error("Invalid Username/Password")
        
        with tab2:
            new_user = st.text_input("New Username", key="new_user")
            new_password = st.text_input("New Password", type='password', key="new_pass")
            if st.button("Create Account"):
                if auth.add_user(new_user, new_password):
                    st.success("Account Created! Please Log In.")
                else:
                    st.warning("User already exists")

def dashboard_page():
    st.title(f"Welcome, {st.session_state['username']}")
    
    # Top Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Scans", "124", "+12%")
    m2.metric("Avg. Confidence", "92%", "+2%")
    m3.metric("Water Saved", "450 Gal", "+5%")
    m4.metric("Fabrics Detected", "8 Types", "Stable")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Stain Distribution")
        df = pd.DataFrame({'Stain': ['Oil', 'Ink', 'Dirt', 'Coffee', 'Blood'], 'Count': [45, 20, 80, 30, 15]})
        fig = px.pie(df, values='Count', names='Stain', hole=0.5, color_discrete_sequence=px.colors.sequential.Bluered)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("System Accuracy Over Time")
        df2 = pd.DataFrame({'Day': range(1, 8), 'Accuracy': [82, 83, 85, 84, 86, 88, 89]})
        fig2 = px.line(df2, x='Day', y='Accuracy', markers=True)
        fig2.update_traces(line_color='#00C9FF')
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig2, use_container_width=True)

def scanner_page(odor_detected=False, uv_fluorescence=False):
    st.markdown("## 📷 Live Fabric Analysis")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Capture Input")
        # Camera Input
        img_file_buffer = st.camera_input("Take a picture of the laundry")
        
        # Or Upload
        uploaded_file = st.file_uploader("Or upload an image", type=['jpg', 'png', 'jpeg'])

    final_image = None
    if img_file_buffer is not None:
        final_image = Image.open(img_file_buffer)
    elif uploaded_file is not None:
        final_image = Image.open(uploaded_file)

    with col2:
        st.markdown("### AI Diagnosis")
        if final_image is not None:
            with st.spinner('AI Neural Network Processing...'):
                # Call Logic
                data = predict_laundry(final_image, odor_detected, uv_fluorescence)
            
            # Display Annotated Image
            st.image(data['annotated_img'], caption="Live Vision Feed (YOLOv8 & PyTorch CNN)", use_column_width=True)
            
            # Display Results Cards
            st.success("Analysis Complete")
            
            res_col1, res_col2, res_col3 = st.columns(3)
            with res_col1:
                st.info(f"**Fabric:** {data['fabric']}\n({data['fabric_conf']*100:.1f}%)")
            with res_col2:
                st.info(f"**Color:** {data['color']}\n({data['color_conf']*100:.1f}%)")
            with res_col3:
                st.warning(f"**Stains:** {data['stains_detected']} Detected")
            
            if odor_detected or uv_fluorescence:
                st.error("🚨 SENSOR OVERRIDE ENGAGED: Invisible threats detected.")
            
            st.markdown("---")
            st.markdown("### 🧼 Recommended Cycle")
            
            # Decision Box
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 15px; border-radius: 12px; color: white; text-align: center; font-size: 1.3rem; font-weight: bold; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.4);">
                Route to: {data['routing_bin']} ({data['wash_instructions']})
            </div>
            """, unsafe_allow_html=True)
            
            # Custom HTML Card for Recommendation
            st.markdown(f"""
            <div style="background: linear-gradient(45deg, #11998e, #38ef7d); padding: 20px; border-radius: 15px; color: black; text-align: center;">
                <h3 style="margin:0; color: #000;">{data['recommendation']['cycle']} Cycle</h3>
                <h2 style="font-size: 3em; margin: 10px 0; color: #000;">{data['recommendation']['temp']}</h2>
                <p style="font-weight: bold; color: #000;">Pre-treat with: {data['recommendation']['detergent']}</p>
            </div>
            """, unsafe_allow_html=True)

# --- MAIN APP LOGIC ---
if not st.session_state['logged_in']:
    login_page()
else:
    # Sidebar Nav
    with st.sidebar:
        st.title("Navigation")
        page = st.radio("Go to", ["Dashboard", "Live Scanner"])
        
        odor_detected = False
        uv_fluorescence = False
        if page == "Live Scanner":
            st.markdown("---")
            st.markdown("### 🎛️ Hardware Sensors")
            st.markdown("Override standard visual AI with simulated physical sensors.")
            odor_detected = st.checkbox("💨 E-Nose (Detect VOC/Odor)")
            uv_fluorescence = st.checkbox("🔦 UV Multispectral")
            
        st.markdown("---")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.experimental_rerun()
            
    if page == "Dashboard":
        dashboard_page()
    elif page == "Live Scanner":
        scanner_page(odor_detected, uv_fluorescence)

