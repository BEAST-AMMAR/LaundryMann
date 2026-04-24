import streamlit as st
import cv2
import numpy as np
from PIL import Image
import torch
import os
from models import LaundryClassifier

st.set_page_config(page_title="Laundry Assistant", page_icon="👚", layout="wide")

@st.cache_resource
def get_classifier():
    return LaundryClassifier()

st.title("👚 Laundry Assistant - Color Sorter")
st.markdown("### Upload a garment image to classify it as **DARK**, **LIGHT**, or **COLORED**.")
st.markdown("---")

# Sidebar
st.sidebar.header("Configuration")
mode = st.sidebar.radio("Display Mode", ["Single Model", "Compare Both Models"])
if mode == "Single Model":
    model_type = st.sidebar.selectbox("Select Model", ["CNN (Deep Learning)", "HSV (Traditional CV)"])

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Uploaded Image")
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True, caption='Input Garment')
    
    # Convert for processing
    img_array = np.array(image.convert('RGB')) 
    classifier = get_classifier()
    
    with col2:
        st.subheader("Classification Results")
        with st.spinner("Classifying..."):
            
            if mode == "Single Model":
                if "CNN" in model_type:
                    if os.path.exists(classifier.model_path):
                        label, conf = classifier.predict_category_cnn(img_array)
                        st.success(f"**CNN Prediction:** {label}")
                        st.info(f"Confidence/Score: {conf}")
                    else:
                        st.warning("CNN Model not trained/found yet. Please train the model.")
                        st.write("Falling back to HSV...")
                        label, conf = classifier.predict_category_hsv(img_array)
                        st.success(f"**HSV Prediction:** {label}")
                        st.info(f"Confidence/Score: {conf}")
                else:
                    label, conf = classifier.predict_category_hsv(img_array)
                    st.success(f"**HSV Prediction:** {label}")
                    st.info(f"Confidence/Score: {conf}")
            else:
                st.markdown("#### Deep Learning (CNN)")
                if os.path.exists(classifier.model_path):
                    label_cnn, conf_cnn = classifier.predict_category_cnn(img_array)
                    st.success(f"Prediction: **{label_cnn}**")
                    st.caption(f"{conf_cnn}")
                else:
                    st.warning("CNN Model not found.")
                
                st.markdown("---")
                st.markdown("#### Traditional CV (HSV)")
                label_hsv, conf_hsv = classifier.predict_category_hsv(img_array)
                st.success(f"Prediction: **{label_hsv}**")
                st.caption(f"{conf_hsv}")
