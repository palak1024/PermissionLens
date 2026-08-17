from fastapi import FastAPI, UploadFile, File
import os
import shutil

# Your APK analyzer
from analyzer import analyze_apk

# Teammate's pipeline
from app.analyzer import analyze

app = FastAPI(
    title="PermissionLens API",
    description="Backend for Android Permission Analyzer",
    version="1.0"
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "PermissionLens Backend is Running 🚀"
    }
@app.post("/analyze")
async def analyze_apk_file(file: UploadFile = File(...)):

    # Save uploaded APK
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract APK information
    apk_info = analyze_apk(file_path)

    # Create the data expected by the Risk Engine
    apk_data = {
        "app_name": apk_info["app_name"],
        "app_purpose": "",      # Frontend can send this later
        "permissions": apk_info["permissions"]
    }

    # Run Risk Engine + AI
    result = analyze(apk_data, include_ai=True)

    return result