import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms
import numpy as np

class SimpleLaundryCNN(nn.Module):
    def __init__(self, num_classes=3):
        super(SimpleLaundryCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(64 * 4 * 4, 128)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = torch.flatten(x, 1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

class ColorClassifier:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.classes = ["COLORED", "DARK", "LIGHT"]
        self.model = SimpleLaundryCNN(num_classes=3)
        self.model.to(self.device)
        
        # Look for laundry_cnn.pth in current directory or workspace root relative to this file
        weight_path = "laundry_cnn.pth"
        if not os.path.exists(weight_path):
            # Check relative to this file's directory: ../../laundry_cnn.pth
            weight_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "laundry_cnn.pth")

        if os.path.exists(weight_path):
            try:
                self.model.load_state_dict(torch.load(weight_path, map_location=self.device))
                self.model.eval()
                print(f"[ColorClassifier] Loaded PyTorch SimpleSimpleLaundryCNN weights from {weight_path}")
            except Exception as e:
                print(f"[ColorClassifier] Failed to load weights from {weight_path}: {e}")
                self.model = None
        else:
            print(f"[WARNING] Color model weights not found at any expected path. Falling back to default.")
            self.model = None

    def predict_color(self, image_np):
        if self.model is None:
            return "LIGHT (Fallback)", 0.85
            
        # Convert numpy array (RGB) to PIL Image
        img_pil = Image.fromarray(image_np)
        
        # Preprocessing matching training transforms (Resize to 32x32 for SimpleLaundryCNN)
        transform = transforms.Compose([
            transforms.Resize((32, 32)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])
        
        img_tensor = transform(img_pil).unsqueeze(0).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(img_tensor)
            probs = torch.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probs, 1)
            
        return self.classes[predicted.item()], confidence.item()

