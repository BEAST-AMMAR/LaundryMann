from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
from PIL import Image
import io
import asyncio
import concurrent.futures

from src.models.stain_detector import StainDetector
from src.models.fabric_classifier import FabricClassifier
from src.models.color_classifier import ColorClassifier
from src.core.decision_engine import LaundryDecisionEngine

from contextlib import asynccontextmanager

import threading

# Global references for models
stain_detector = None
fabric_classifier = None
color_classifier = None
decision_engine = None
executor = None

def load_models_background():
    global stain_detector, fabric_classifier, color_classifier, decision_engine, executor
    print("Loading Machine Learning Models in background thread...")
    try:
        stain_detector = StainDetector()
        fabric_classifier = FabricClassifier()
        color_classifier = ColorClassifier()
        decision_engine = LaundryDecisionEngine()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        print("All models loaded successfully!")
    except Exception as e:
        print("Failed to load models:", e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Spawn thread to load models so Uvicorn can bind to port 8000 instantly
    t = threading.Thread(target=load_models_background, daemon=True)
    t.start()
    yield
    print("Shutting down models...")
    if executor:
        executor.shutdown(wait=True)

app = FastAPI(
    title="Advanced Laundry AI API",
    description="Multi-stage ensemble pipeline for robotic laundry sorting.",
    version="2.0.0",
    lifespan=lifespan
)


@app.post("/analyze")
async def analyze_garment(
    file: UploadFile = File(...),
    odor_detected: bool = Form(False),
    uv_fluorescence: bool = Form(False)
):
    """
    Analyzes a garment image concurrently across all models.
    """
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    img_array = np.array(image.convert('RGB'))

    # Run the models concurrently
    loop = asyncio.get_event_loop()
    
    # We use executor to offload CPU-bound PyTorch tasks
    stain_task = loop.run_in_executor(executor, stain_detector.detect_stains, img_array)
    fabric_task = loop.run_in_executor(executor, fabric_classifier.predict_fabric, img_array)
    color_task = loop.run_in_executor(executor, color_classifier.predict_color, img_array)
    
    # Wait for all models to finish (happens simultaneously)
    stain_result, fabric_result, color_result = await asyncio.gather(stain_task, fabric_task, color_task)
    
    stains, annotated_img = stain_result
    fabric_label, fabric_conf = fabric_result
    color_label, color_conf = color_result

    # Pass outputs to the deterministic Decision Engine
    routing_bin, wash_instructions = decision_engine.decide_routing(
        color=color_label,
        fabric=fabric_label,
        stains=stains,
        odor_detected=odor_detected,
        uv_fluorescence=uv_fluorescence
    )

    import base64
    from PIL import Image
    import io
    
    # Encode annotated image to base64 for frontend
    try:
        pil_img = Image.fromarray(annotated_img)
        buffered = io.BytesIO()
        pil_img.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception:
        img_base64 = None

    return JSONResponse(content={
        "status": "success",
        "annotated_image": img_base64,
        "analysis": {
            "color": {"prediction": color_label, "confidence": color_conf},
            "fabric": {"prediction": fabric_label, "confidence": fabric_conf},
            "stains_detected": len(stains),
            "stain_details": stains
        },
        "sensors": {
            "odor_detected": odor_detected,
            "uv_fluorescence_detected": uv_fluorescence
        },
        "decision": {
            "routing_bin": routing_bin,
            "instructions": wash_instructions
        }
    })

# Mount the static files directory at the root
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

