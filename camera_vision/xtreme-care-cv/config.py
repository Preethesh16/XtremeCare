# config.py — all tunable constants for XtremeCare CV pipeline

# Face recognition
FACE_CONFIDENCE_THRESHOLD = 0.85

# Hand-to-mouth verification
# Normalized to frame height; smaller = stricter proximity required
MOUTH_DISTANCE_THRESHOLD = 0.15

# How long to wait for intake verification before marking MISSED
VERIFICATION_WINDOW_SECONDS = 30

# Webcam
WEBCAM_INDEX = 0          # Change to 1 if laptop camera conflicts with external
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Patient
PATIENT_ID = "patient_001"
PATIENT_NAME = "Patient"

# Paths
DB_PATH = "xtreme_care.db"
MODEL_PATH = "models/face_model.pt"
DATA_DIR = "data/patients"

# MediaPipe model files (new Tasks API — mediapipe >= 0.10.21)
HAND_LANDMARKER_PATH = "models/hand_landmarker.task"
FACE_LANDMARKER_PATH = "models/face_landmarker.task"

# Backend API
API_BASE_URL = "http://localhost:8000"
