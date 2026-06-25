from ultralytics import YOLO
import os

def train_yolo_stain_model():
    print("Step 1: Locating Real Dataset...")
    
    # THIS IS WHERE YOU EXTRACT THE DOWNLOADED DATASET!
    dataset_yaml = os.path.join("datasets", "real_stains", "data.yaml")
    
    if not os.path.exists(dataset_yaml):
        print(f"ERROR: Could not find the dataset at {dataset_yaml}")
        print("Please download the YOLO dataset and extract it into the 'datasets/real_stains' folder.")
        return

    print(f"Found real dataset at {dataset_yaml}!")
    print("\nStep 2: Initializing YOLOv8 Model...")
    # Load a model. Using YOLOv8 nano for speed
    model = YOLO('yolov8n.pt')
    
    print("\nStep 3: Starting Training Loop on Real Data...")
    # Train the model. We increase epochs for real data.
    results = model.train(
        data=dataset_yaml,
        epochs=50, # Increased for real dataset
        imgsz=640,
        batch=16,
        name='real_stain_model',
        device='cpu' # Using CPU so it runs safely on any machine without failing on CUDA errors
    )
    
    print("\nTraining Complete! Model weights saved to runs/detect/real_stain_model/weights/best.pt")

if __name__ == "__main__":
    train_yolo_stain_model()
