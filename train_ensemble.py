from ultralytics import YOLO
import os
import shutil
import random

def auto_split_classification_dataset(source_dir, output_dir, split_ratio=0.8):
    """
    Checks if a dataset is split into train/val. If not, it creates a new structured
    directory and moves the files.
    """
    if os.path.exists(os.path.join(source_dir, 'train')) and os.path.exists(os.path.join(source_dir, 'val')):
        return source_dir # Already split!
    
    print(f"Auto-splitting raw dataset at {source_dir} into train/val...")
    os.makedirs(output_dir, exist_ok=True)
    
    train_dir = os.path.join(output_dir, 'train')
    val_dir = os.path.join(output_dir, 'val')
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(val_dir, exist_ok=True)
    
    classes = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]
    for cls in classes:
        os.makedirs(os.path.join(train_dir, cls), exist_ok=True)
        os.makedirs(os.path.join(val_dir, cls), exist_ok=True)
        
        cls_dir = os.path.join(source_dir, cls)
        images = [f for f in os.listdir(cls_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        random.shuffle(images)
        
        split_index = int(len(images) * split_ratio)
        train_imgs = images[:split_index]
        val_imgs = images[split_index:]
        
        for img in train_imgs:
            shutil.copy(os.path.join(cls_dir, img), os.path.join(train_dir, cls, img))
        for img in val_imgs:
            shutil.copy(os.path.join(cls_dir, img), os.path.join(val_dir, cls, img))
            
    print(f"Dataset split complete! Saved to {output_dir}")
    return output_dir

def train_ensemble():
    # ---------------------------------------------------------
    # MODEL 1: STAIN DETECTION (Object Detection)
    # ---------------------------------------------------------
    stain_data_yaml = os.path.abspath(os.path.join("datasets", "real_stains", "data.yaml"))
    if os.path.exists(stain_data_yaml):
        print("\n\n" + "="*50)
        print("🚀 TRAINING MODEL 1/3: Stain Detector (YOLOv8-Detect)")
        print("="*50)
        stain_model = YOLO('yolov8n.pt')
        stain_model.train(
            data=stain_data_yaml,
            epochs=20, # Reduced to 20 so it runs reasonably fast on CPU for prototyping
            imgsz=640,
            batch=16,
            name='stain_detector_v1',
            device='cpu'
        )
    else:
        print(f"Skipping Stain Training: {stain_data_yaml} not found.")

    # ---------------------------------------------------------
    # MODEL 2: APPAREL CLASSIFICATION (Image Classification)
    # ---------------------------------------------------------
    apparel_raw_dir = os.path.abspath(os.path.join("data", "fashion apparels", "Apparel images dataset new"))
    apparel_split_dir = os.path.abspath(os.path.join("datasets", "apparel_split"))
    
    if os.path.exists(apparel_raw_dir):
        print("\n\n" + "="*50)
        print("👕 TRAINING MODEL 2/3: Apparel Classifier (YOLOv8-Classify)")
        print("="*50)
        final_apparel_dir = auto_split_classification_dataset(apparel_raw_dir, apparel_split_dir)
        
        apparel_model = YOLO('yolov8n-cls.pt')
        apparel_model.train(
            data=final_apparel_dir,
            epochs=10, 
            imgsz=224,
            name='apparel_classifier_v1',
            device='cpu'
        )
    else:
        print(f"Skipping Apparel Training: {apparel_raw_dir} not found.")

    # ---------------------------------------------------------
    # MODEL 3: COLOR CLASSIFICATION (Image Classification)
    # ---------------------------------------------------------
    color_dir = os.path.abspath("laundry_data")
    if os.path.exists(color_dir):
        print("\n\n" + "="*50)
        print("🎨 TRAINING MODEL 3/3: Color Classifier (YOLOv8-Classify)")
        print("="*50)
        color_model = YOLO('yolov8n-cls.pt')
        color_model.train(
            data=color_dir,
            epochs=10,
            imgsz=224,
            name='color_classifier_v1',
            device='cpu'
        )
    else:
        print(f"Skipping Color Training: {color_dir} not found.")

    print("\n\n✅ ENSEMBLE TRAINING COMPLETE!")
    print("All weights saved successfully to runs/detect/ and runs/classify/")

if __name__ == "__main__":
    train_ensemble()
