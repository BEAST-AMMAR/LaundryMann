from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import cv2
import numpy as np
from PIL import Image
import io
from models import LaundryClassifier

app = FastAPI(
    title="Laundry Assistant API",
    description="API for classifying laundry images into DARK, LIGHT, or COLORED categories using CNN and HSV models.",
    version="1.0.0"
)

# Initialize the classifier
classifier = LaundryClassifier()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Laundry Assistant API. Use /predict for predictions."}

@app.post("/predict")
async def predict(file: UploadFile = File(...), model_type: str = "CNN"):
    """
    Predict the laundry category for an uploaded image.
    - file: The image file (jpg, jpeg, png)
    - model_type: 'CNN' or 'HSV' (default: CNN)
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPEG or PNG image.")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert for processing
        img_array = np.array(image.convert('RGB')) 

        if model_type.upper() == "CNN":
            label, conf = classifier.predict_category_cnn(img_array)
            return JSONResponse(content={"model": "CNN", "prediction": label, "confidence": conf})
        elif model_type.upper() == "HSV":
            label, conf = classifier.predict_category_hsv(img_array)
            return JSONResponse(content={"model": "HSV", "prediction": label, "score": conf})
        else:
            raise HTTPException(status_code=400, detail="Invalid model_type. Choose 'CNN' or 'HSV'.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
