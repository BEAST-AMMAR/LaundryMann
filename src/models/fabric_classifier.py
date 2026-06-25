import os
from ultralytics import YOLO

class FabricClassifier:
    def __init__(self):
        # We will use the trained YOLOv8-cls model
        weight_path = os.path.join("runs", "classify", "apparel_classifier_v1", "weights", "best.pt")
        
        self.model = None
        if os.path.exists(weight_path):
            self.model = YOLO(weight_path)
            print(f"[FabricClassifier] Loaded YOLOv8 classification weights from {weight_path}")
        else:
            print(f"[WARNING] Fabric model weights not found at {weight_path}. Run train_ensemble.py first.")

    def predict_fabric(self, image_np):
        if self.model is None:
            return "Cotton (Fallback)", 0.65
            
        results = self.model(image_np, verbose=False)
        result = results[0]
        
        # Get the highest confidence class
        top_class_id = result.probs.top1
        top_class_name = result.names[top_class_id]
        confidence = result.probs.top1conf.item()
        
        return top_class_name, confidence
