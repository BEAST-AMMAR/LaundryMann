# 👚 AIML CV Project: Laundry Assistant - Color Sorter

## Project Goal
To develop and compare two Computer Vision models (Traditional HSV vs. Deep Learning CNN) for automatically classifying garments into three laundry categories: **DARK, LIGHT, and COLORED**.

## Technical Components
1. **Traditional CV Baseline:** Rule-based classification using the **HSV (Hue, Saturation, Value) color space** thresholds.
2. **Deep Learning Model:** A custom, lightweight **Convolutional Neural Network (CNN)** trained end-to-end using PyTorch.

## Setup Instructions (Google Colab / "Antigravity")

1. **Create Project Structure:** Create a folder named `AIML_CV_Laundry_Sorter`.
2. **Populate Files:** Save the provided Python code snippets into the files `laundry_assistant.ipynb`, `requirements.txt`, etc.
3. **Dataset (Crucial):** Create a subfolder named `laundry_data/` with two subdirectories: `train/` and `val/`. Inside `train/` and `val/`, create three folders: `DARK`, `LIGHT`, and `COLORED`, and populate them with images of clothes for each category.
4. **Run Notebook:** Open `laundry_assistant.ipynb` in Google Colab, change the runtime to **T4 GPU**, and run all cells sequentially.

## Deliverables for Report
* **Code:** Fully documented and runnable Colab notebook.
* **Analysis:** Comparison of performance metrics (Accuracy, Robustness) between the CNN and the HSV model (Section 4 in your report).
* **Demonstration:** Visual outputs showing the classification results for both models on sample images.