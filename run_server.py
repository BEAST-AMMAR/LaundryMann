import uvicorn
import os
import sys

workspace = r"f:\onedrive backup\OneDrive\Desktop\laundry assist"
os.chdir(workspace)
sys.path.insert(0, workspace)

if __name__ == "__main__":
    print("Starting Uvicorn programmatically...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000)
