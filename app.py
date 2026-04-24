import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import os
from PIL import Image, ImageTk
from models import LaundryClassifier

classifier = LaundryClassifier()

class LaundryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Laundry Assistant - Color Sorter")
        self.geometry("600x600")
        self.configure(bg="#f0f0f0")

        self.image_path = None
        self.image_panel = None
        self.result_label = None
        self.model_type = tk.StringVar(value="CNN")  # Default to CNN

        self.create_widgets()

    def create_widgets(self):
        # Title
        title = tk.Label(self, text="👚 Laundry Color Sorter", font=("Arial", 16, "bold"), bg="#f0f0f0")
        title.pack(pady=10)

        # Radio buttons for model selection
        models_frame = tk.Frame(self, bg="#f0f0f0")
        models_frame.pack(pady=5)
        tk.Radiobutton(models_frame, text="CNN (Deep Learning)", variable=self.model_type, value="CNN", bg="#f0f0f0").pack(side=tk.LEFT)
        tk.Radiobutton(models_frame, text="HSV (Traditional CV)", variable=self.model_type, value="HSV", bg="#f0f0f0").pack(side=tk.LEFT)

        # Button to select image
        select_btn = tk.Button(self, text="Select Image", command=self.select_image, font=("Arial", 12))
        select_btn.pack(pady=10)

        # Panel to display image
        self.image_panel = tk.Label(self, bg="#f0f0f0")
        self.image_panel.pack(pady=10)

        # Label to display result
        self.result_label = tk.Label(self, text="", font=("Arial", 14), bg="#f0f0f0")
        self.result_label.pack(pady=10)

        # Train model button
        train_btn = tk.Button(self, text="Train Model (if needed)", command=self.train_model, font=("Arial", 12))
        train_btn.pack(pady=10)

        # Exit button
        exit_btn = tk.Button(self, text="Exit", command=self.quit, font=("Arial", 12))
        exit_btn.pack(pady=10)

    def select_image(self):
        file_path = filedialog.askopenfilename(title="Select an image", filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            self.image_path = file_path
            self.display_image(file_path)
            self.run_classification()

    def display_image(self, path):
        img = Image.open(path)
        img = img.resize((300, 300), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        self.image_panel.config(image=img_tk)
        self.image_panel.image = img_tk

    def classify_image(self, image, model_type):
        try:
            if model_type == "CNN":
                return classifier.predict_category_cnn(image)
            elif model_type == "HSV":
                return classifier.predict_category_hsv(image)
            else:
                return "Unknown", "Invalid model type"
        except Exception as e:
            return "Error", str(e)

    def run_classification(self):
        if self.image_path and os.path.exists(self.image_path):
            image = cv2.imread(self.image_path)
            result, category = self.classify_image(image, self.model_type.get())
            self.result_label.config(text=f"Category: {result} ({category})")
        else:
            self.result_label.config(text="Please select an image first.")

    def train_model(self):
        try:
            messagebox.showinfo("Training", "Training CNN model. This may take a few minutes...")
            classifier.train_model()
            messagebox.showinfo("Training Complete", "Model training completed!")
            self.run_classification()
        except Exception as e:
            messagebox.showerror("Training Error", f"Error during training: {str(e)}")

    def on_select_image(self, event=None):
        self.run_classification()

if __name__ == "__main__":
    app = LaundryApp()
    app.mainloop()
