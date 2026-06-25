# LaundryMann AI

LaundryMann is a next-generation AI-powered laundry assistant designed to eliminate laundry anxiety and prevent clothing damage. It features an ultra-modern, enterprise-grade dark mode UI and leverages multiple advanced machine learning models to analyze garments, identify stains, read care labels, and generate personalized, step-by-step washing instructions.

## 🚀 Key Features

*   **Dark Mode Masterpiece UI:** A breathtaking, hardcore "Linear-style" user interface built with advanced Streamlit CSS injection. It features inset shadows, glowing borders, and buttery-smooth micro-animations.
*   **Persistent User Authentication:** Secure account creation and login system powered by `bcrypt` hashing, allowing users to safely manage their Digital Wardrobe.
*   **Live YOLOv8 Scanner:** A real-time bounding-box visualizer that scans a laundry basket to detect and count multiple clothing items instantly.
*   **Fabric & Color Classification:** AI models that analyze uploaded images to identify the fabric type (Cotton, Silk, Wool, etc.) and dominant color profile.
*   **Advanced Stain Detection:** Intelligently identifies the type of stain (Coffee, Wine, Oil, etc.) and cross-references it with the fabric type to recommend precise stain-removal chemicals.
*   **OCR Care Label Reading:** Extracts text from physical care labels to ensure the generated washing parameters strictly adhere to manufacturer guidelines.
*   **PDF Report Generation:** Instantly export your personalized washing guides into a beautiful, downloadable PDF report.

## 🛠️ Technology Stack

*   **Frontend:** Streamlit (with aggressive CSS override architecture)
*   **Backend / API:** FastAPI (Uvicorn)
*   **Machine Learning Pipeline:** 
    *   Ultralytics YOLOv8 (Live Object Detection)
    *   OpenCV / Pillow (Image Processing)
    *   Tesseract OCR (Care Label Extraction)
    *   Scikit-Learn (Classification Mockups)
*   **Database & Authentication:** SQLite, Passlib (bcrypt), Extra-Streamlit-Components (Cookie Session Management)

## 📦 Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/BEAST-AMMAR/LaundryMann.git
    cd "LaundryMann"
    ```

2.  **Install Dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ensure Tesseract OCR is Installed:**
    *   Windows: Download the installer from the UB-Mannheim repository and add the executable to your System PATH.
    *   Linux: `sudo apt-get install tesseract-ocr`
    *   macOS: `brew install tesseract`

## 🏃 Running the Application

To experience the full capability of LaundryMann, run the main Streamlit application:

```bash
python launch_streamlit.py
```
*(Note: We use a custom launcher script to handle Streamlit execution dynamically on local environments.)*

Alternatively, you can run the backend API independently if you are looking to integrate the AI models into another service:

```bash
uvicorn api:app --reload
```

## 🔒 Authentication Note
User sessions are maintained using browser cookies. The `wardrobe.db` SQLite database is intentionally ignored by `.gitignore` to prevent sensitive user hash data from being exposed in source control. 

## 🎨 UI/UX Philosophy
The frontend of this application completely overrides the standard Streamlit components to deliver a "Midnight Obsidian" aesthetic. The interface acts as a blank canvas, populated with HTML/CSS components built to rival modern multi-million dollar SaaS platforms.

---
*Built with passion for flawless clothing care and pristine UI engineering.*