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

# --- MOCK INFERENCE FUNCTION (Replace with your actual CNN import) ---
def predict_laundry(image):
    # This simulates your CNN + HSV logic delay
    time.sleep(1) 
    
    # Mock Logic for Demo Purposes (Replace this block with your model inference)
    # img_tensor = preprocess(image)
    # pred = model(img_tensor)
    
    # Returning random consistent results for UI demo
    results = {
        "fabric": "Silk",
        "stain": "Oil Stain",
        "confidence": 0.88,
        "recommendation": {
            "temp": "30°C",
            "cycle": "Delicate",
            "detergent": "Enzyme-based"
        }
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

def scanner_page():
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
            # Display Image
            st.image(final_image, caption="Input Image", use_column_width=True)
            
            with st.spinner('AI Neural Network Processing...'):
                # Call Logic
                data = predict_laundry(final_image)
            
            # Display Results Cards
            st.success("Analysis Complete")
            
            res_col1, res_col2 = st.columns(2)
            with res_col1:
                st.info(f"**Fabric:** {data['fabric']}")
                st.info(f"**Stain:** {data['stain']}")
            with res_col2:
                st.warning(f"**Confidence:** {int(data['confidence']*100)}%")
            
            st.markdown("---")
            st.markdown("### 🧼 Recommended Cycle")
            
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
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.experimental_rerun()
            
    if page == "Dashboard":
        dashboard_page()
    elif page == "Live Scanner":
        scanner_page()