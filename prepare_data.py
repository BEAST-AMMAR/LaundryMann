import os
import cv2
import numpy as np
import yaml
import shutil

def create_synthetic_yolo_dataset(base_dir="yolo_dataset", num_images=50):
    """
    Creates a synthetic toy dataset to demonstrate the YOLOv8 training loop.
    Generates images with random colored 'stains' (ellipses/polygons) and YOLO format labels.
    """
    print(f"Creating synthetic dataset in {base_dir}...")
    
    # Create directories
    for split in ['train', 'val']:
        os.makedirs(os.path.join(base_dir, 'images', split), exist_ok=True)
        os.makedirs(os.path.join(base_dir, 'labels', split), exist_ok=True)

    classes = ['stain_oil', 'stain_blood', 'stain_rust']
    
    # Generate config yaml
    yaml_data = {
        'path': os.path.abspath(base_dir),
        'train': 'images/train',
        'val': 'images/val',
        'nc': len(classes),
        'names': classes
    }
    
    yaml_path = os.path.join(base_dir, 'data.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f)
        
    # Generate images and labels
    img_size = 640
    for i in range(num_images):
        split = 'train' if i < int(num_images * 0.8) else 'val'
        
        # Create a background (simulating fabric)
        bg_color = np.random.randint(150, 255, size=(3,)).tolist()
        img = np.full((img_size, img_size, 3), bg_color, dtype=np.uint8)
        
        labels = []
        # Add 1 to 3 random stains
        for _ in range(np.random.randint(1, 4)):
            class_id = np.random.randint(0, len(classes))
            # Random position
            cx = np.random.randint(50, img_size - 50)
            cy = np.random.randint(50, img_size - 50)
            # Random size
            w = np.random.randint(20, 150)
            h = np.random.randint(20, 150)
            
            # Draw stain
            stain_color = [0,0,0]
            if class_id == 0: stain_color = [50, 50, 50] # Oil (Dark)
            if class_id == 1: stain_color = [0, 0, 150] # Blood (Red)
            if class_id == 2: stain_color = [0, 100, 200] # Rust (Orange/Brown)
            
            cv2.ellipse(img, (cx, cy), (w//2, h//2), np.random.randint(0, 360), 0, 360, stain_color, -1)
            
            # YOLO format: class_id cx_norm cy_norm w_norm h_norm
            labels.append(f"{class_id} {cx/img_size} {cy/img_size} {w/img_size} {h/img_size}")
            
        # Save image and label
        img_name = f"synth_{i}.jpg"
        cv2.imwrite(os.path.join(base_dir, 'images', split, img_name), img)
        with open(os.path.join(base_dir, 'labels', split, img_name.replace('.jpg', '.txt')), 'w') as f:
            f.write('\n'.join(labels))
            
    print(f"Synthetic dataset created successfully at {yaml_path}")
    return yaml_path

if __name__ == "__main__":
    create_synthetic_yolo_dataset()
