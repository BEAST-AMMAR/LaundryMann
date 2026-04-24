import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import cv2
import numpy as np
import os
from PIL import Image

# HSV Ranges (from HSV threshhold.py)
HSV_RANGES = {
    "DARK": {"lower": np.array([0, 0, 0]), "upper": np.array([179, 255, 70])},
    "LIGHT": {"lower": np.array([0, 0, 180]), "upper": np.array([179, 60, 255])},
    "COLORED": {"lower": np.array([0, 60, 70]), "upper": np.array([179, 255, 180])}
}

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

class LaundryClassifier:
    def __init__(self):
        self.model = SimpleLaundryCNN()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model_path = "laundry_cnn.pth"
        self.classes = ["COLORED", "DARK", "LIGHT"] # Alphabetical order usually for ImageFolder
        
        if os.path.exists(self.model_path):
            try:
                self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
                self.model.eval()
                print("Loaded existing model.")
            except Exception as e:
                print(f"Failed to load model: {e}")

    def train_model(self, data_dir="laundry_data"):
        print("Starting training...")
        train_dir = os.path.join(data_dir, "train")
        val_dir = os.path.join(data_dir, "val")
        
        if not os.path.exists(train_dir):
            print(f"Data directory {train_dir} not found!")
            return

        transform = transforms.Compose([
            transforms.Resize((32, 32)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])

        train_dataset = datasets.ImageFolder(train_dir, transform=transform)
        # Verify classes
        self.classes = train_dataset.classes
        print(f"Classes found: {self.classes}")
        
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        epochs = 5
        self.model.train()
        
        for epoch in range(epochs):
            running_loss = 0.0
            for i, data in enumerate(train_loader, 0):
                inputs, labels = data
                inputs, labels = inputs.to(self.device), labels.to(self.device)

                optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
            
            print(f"Epoch {epoch+1}, Loss: {running_loss/len(train_loader)}")

        torch.save(self.model.state_dict(), self.model_path)
        print("Finished Training and saved model.")

    def predict_category_cnn(self, image_input):
        # image_input can be numpy array (BGR from cv2)
        if isinstance(image_input, np.ndarray):
            # Convert BGR to RGB and PIL
            image_input = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB)
            image_input = Image.fromarray(image_input)
            
        transform = transforms.Compose([
            transforms.Resize((32, 32)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])
        
        img_tensor = transform(image_input).unsqueeze(0).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(img_tensor)
            _, predicted = torch.max(outputs, 1)
            
        return self.classes[predicted.item()], "CNN Confidence"

    def predict_category_hsv(self, image_input):
        # Expecting BGR numpy array
        if not isinstance(image_input, np.ndarray):
            # Try to convert PIL to np array BGR
            image_input = np.array(image_input)
            image_input = cv2.cvtColor(image_input, cv2.COLOR_RGB2BGR)

        img_hsv = cv2.cvtColor(image_input, cv2.COLOR_BGR2HSV)
        max_score = 0
        predicted_class = "UNKNOWN"

        for name, limits in HSV_RANGES.items():
            mask = cv2.inRange(img_hsv, limits["lower"], limits["upper"])
            pixel_count = cv2.countNonZero(mask)
            proportion = pixel_count / (image_input.shape[0] * image_input.shape[1])
            
            if proportion > max_score:
                max_score = proportion
                predicted_class = name
        
        return predicted_class, f"Score: {max_score:.2f}"