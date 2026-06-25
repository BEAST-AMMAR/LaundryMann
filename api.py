from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import numpy as np
from PIL import Image
import io
import asyncio
import concurrent.futures

from src.models.stain_detector import StainDetector
from src.models.fabric_classifier import FabricClassifier
from src.models.color_classifier import ColorClassifier
from src.core.decision_engine import LaundryDecisionEngine
from src.models.ocr_reader import OCRReader
from src.models.clothing_detector import ClothingDetector
from src.database import get_db, WardrobeItem, User

from contextlib import asynccontextmanager
import threading
import base64

# Global references for models
stain_detector = None
fabric_classifier = None
color_classifier = None
decision_engine = None
ocr_reader = None
clothing_detector = None
executor = None

def load_models_background():
    global stain_detector, fabric_classifier, color_classifier, decision_engine
    global ocr_reader, clothing_detector, executor
    print("Loading Machine Learning Models in background thread...")
    try:
        stain_detector = StainDetector()
        fabric_classifier = FabricClassifier()
        color_classifier = ColorClassifier()
        decision_engine = LaundryDecisionEngine()
        ocr_reader = OCRReader()
        clothing_detector = ClothingDetector()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        print("All models loaded successfully!")
    except Exception as e:
        print("Failed to load models:", e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    t = threading.Thread(target=load_models_background, daemon=True)
    t.start()
    yield
    print("Shutting down models...")
    if executor:
        executor.shutdown(wait=True)

app = FastAPI(
    title="Advanced Laundry AI API",
    description="Multi-stage ensemble pipeline for robotic laundry sorting.",
    version="3.0.0",
    lifespan=lifespan
)

def encode_image(img_array):
    try:
        pil_img = Image.fromarray(img_array)
        buffered = io.BytesIO()
        pil_img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception:
        return None

@app.post("/analyze")
async def analyze_garment(
    file: UploadFile = File(...),
    odor_detected: bool = Form(False),
    uv_fluorescence: bool = Form(False)
):
    """
    Analyzes a single garment image concurrently across all models.
    """
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    img_array = np.array(image.convert('RGB'))

    loop = asyncio.get_event_loop()
    
    stain_task = loop.run_in_executor(executor, stain_detector.detect_stains, img_array)
    fabric_task = loop.run_in_executor(executor, fabric_classifier.predict_fabric, img_array)
    color_task = loop.run_in_executor(executor, color_classifier.predict_color, img_array)
    
    stain_result, fabric_result, color_result = await asyncio.gather(stain_task, fabric_task, color_task)
    
    stains, annotated_img = stain_result
    fabric_label, fabric_conf = fabric_result
    color_label, color_conf = color_result

    routing_bin, wash_instructions = decision_engine.decide_routing(
        color=color_label,
        fabric=fabric_label,
        stains=stains,
        odor_detected=odor_detected,
        uv_fluorescence=uv_fluorescence
    )

    img_base64 = encode_image(annotated_img)

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

@app.post("/analyze_basket")
async def analyze_basket(file: UploadFile = File(...)):
    """
    Detects multiple items in a basket, analyzes each, and returns a safety report.
    """
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    img_array = np.array(image.convert('RGB'))
    
    crops = clothing_detector.extract_garments(img_array)
    results = []
    
    # Process each detected crop
    for crop in crops:
        stains, _ = stain_detector.detect_stains(crop)
        fabric_label, _ = fabric_classifier.predict_fabric(crop)
        color_label, _ = color_classifier.predict_color(crop)
        results.append({
            "color": color_label,
            "fabric": fabric_label,
            "stains": stains
        })
        
    safety_report = clothing_detector.check_mixed_safety(results)
    
    return JSONResponse(content={
        "status": "success",
        "items_detected": len(crops),
        "item_results": results,
        "safety_report": safety_report
    })

@app.post("/analyze_tag")
async def analyze_tag(file: UploadFile = File(...)):
    """
    Reads OCR from a care label tag.
    """
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    img_array = np.array(image.convert('RGB'))
    
    text = ocr_reader.read_care_label(img_array)
    instructions = ocr_reader.parse_care_instructions(text)
    
    return JSONResponse(content={
        "status": "success",
        "raw_text": text,
        "parsed_instructions": instructions
    })

@app.post("/wardrobe/add")
async def add_to_wardrobe(
    color: str = Form(...),
    fabric: str = Form(...),
    stain_status: str = Form(...),
    wash_instructions: str = Form(...),
    db: Session = Depends(get_db)
):
    item = WardrobeItem(
        color=color,
        fabric=fabric,
        stain_status=stain_status,
        wash_instructions=wash_instructions
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

# Mount the static files directory at the root
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
