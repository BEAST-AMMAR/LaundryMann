import os
import cv2
import numpy as np
import shutil
import random

# Source directories
SOURCE_DIRS = [
    r"f:/onedrive backup/OneDrive/Desktop/laundry assist/data/fashion apparels/Apparel images dataset new",
    r"f:/onedrive backup/OneDrive/Desktop/laundry assist/data/fabric strain/images"
]

# Destination directory
BASE_DIR = r"f:/onedrive backup/OneDrive/Desktop/laundry assist/laundry_data"
TRAIN_DIR = os.path.join(BASE_DIR, "train")
VAL_DIR = os.path.join(BASE_DIR, "val")

CLASSES = ["DARK", "LIGHT", "COLORED"]

# HSV Ranges (Exact copy to ensure consistency)
HSV_RANGES = {
    "DARK": {"lower": np.array([0, 0, 0]), "upper": np.array([179, 255, 70])},
    "LIGHT": {"lower": np.array([0, 0, 180]), "upper": np.array([179, 60, 255])},
    "COLORED": {"lower": np.array([0, 60, 70]), "upper": np.array([179, 255, 180])}
}

def classify_hsv(img_path):
    try:
        img_bgr = cv2.imread(img_path)
        if img_bgr is None: return None
        
        # Resize for speed
        img_bgr = cv2.resize(img_bgr, (64, 64))
        
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        max_score = 0
        predicted_class = "COLORED" # Default fallback

        for name, limits in HSV_RANGES.items():
            mask = cv2.inRange(img_hsv, limits["lower"], limits["upper"])
            pixel_count = cv2.countNonZero(mask)
            proportion = pixel_count / (img_bgr.shape[0] * img_bgr.shape[1])
            
            if proportion > max_score:
                max_score = proportion
                predicted_class = name
        
        return predicted_class
    except Exception as e:
        print(f"Error processing {img_path}: {e}")
        return None

def main():
    # Create dirs
    for d in [TRAIN_DIR, VAL_DIR]:
        for c in CLASSES:
            os.makedirs(os.path.join(d, c), exist_ok=True)

    images_found = 0
    images_processed = 0

    for source in SOURCE_DIRS:
        if not os.path.exists(source):
            print(f"Source not found: {source}")
            continue

        for root, dirs, files in os.walk(source):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    images_found += 1
                    file_path = os.path.join(root, file)
                    
                    category = classify_hsv(file_path)
                    if not category:
                        continue

                    # Split train/val
                    dest_dir = TRAIN_DIR if random.random() > 0.2 else VAL_DIR
                    target_path = os.path.join(dest_dir, category, f"{images_processed}_{file}")
                    
                    shutil.copy2(file_path, target_path)
                    images_processed += 1
                    
                    if images_processed % 100 == 0:
                        print(f"Processed {images_processed} images...")

    print(f"Done! Found {images_found}, Processed {images_processed}.")
    for c in CLASSES:
        print(f"Train {c}: {len(os.listdir(os.path.join(TRAIN_DIR, c)))}")
        print(f"Val {c}: {len(os.listdir(os.path.join(VAL_DIR, c)))}")

if __name__ == "__main__":
    main()
