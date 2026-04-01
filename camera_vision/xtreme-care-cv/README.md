# XtremeCare — Computer Vision Pipeline

AI-enabled medication adherence verification using YOLOv8 face detection and MediaPipe hand tracking.

---

## Requirements

- **Python 3.14.x** (tested on 3.14.3)
- Webcam (built-in or USB)
- 4 GB RAM minimum (8 GB recommended for training)

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

All packages in `requirements.txt` use `>=` floor pins — pip resolves the newest
version compatible with Python 3.14 automatically.

> **mediapipe note:** If pip says "No matching distribution found for mediapipe"
> on Python 3.14, run:
> ```bash
> pip install mediapipe --pre
> ```
> or install from the official mediapipe GitHub release page.
> The system still works without mediapipe — hand/mouth detection will be
> disabled and sessions will auto-timeout instead.

---

## Usage — 3 steps

### Step 1 — Capture patient face photos

```bash
python capture.py
```

- Auto-captures 30 photos + 4 augmented variants each = **120 images total**
- Saved to `data/patients/patient_001/raw/`
- A yellow guide box shows where to position your face
- Press **Q** to quit early

> Wrong camera? Change `WEBCAM_INDEX = 1` (or 2) in `config.py`

### Step 2 — Train the recognition model

```bash
python train.py
```

- Splits images 80/20 into train/val
- Downloads `yolov8n.pt` base weights (~6 MB, once only)
- Fine-tunes on CPU — **30–45 minutes** on a typical laptop
- Saves best weights to `models/face_model.pt`

### Step 3 — Run the full pipeline

```bash
python main.py
```

- Opens webcam with live HUD
- **Press SPACE** to simulate a dose dispense event
- 30-second window to verify the patient took medication:
  1. YOLOv8 recognises the patient's face
  2. MediaPipe detects hand moving near mouth
- Result (VERIFIED / MISSED) written to `xtreme_care.db` and POSTed to backend
- **Press Q** to quit

---

## config.py — Tunable Parameters

| Parameter | Default | What it controls |
|---|---|---|
| `FACE_CONFIDENCE_THRESHOLD` | `0.85` | YOLO confidence needed to count as valid face. Lower to `0.70` if patient is missed; raise if strangers are matched. |
| `MOUTH_DISTANCE_THRESHOLD` | `0.15` | Normalised wrist-to-mouth distance (0–1) to trigger VERIFIED. Increase if gesture isn't firing; decrease if false-positives appear. |
| `VERIFICATION_WINDOW_SECONDS` | `30` | Seconds to wait for intake gesture before MISSED. |
| `WEBCAM_INDEX` | `0` | OpenCV camera index. Change to `1` or `2` if wrong camera opens. |
| `FRAME_WIDTH / FRAME_HEIGHT` | `640 / 480` | Capture resolution. Reduce to `320×240` on Pi if CPU is too slow. |
| `PATIENT_ID` | `"patient_001"` | Used for DB records and folder paths. Change when registering a new patient. |
| `PATIENT_NAME` | `"Patient"` | Display name on face-box label. |
| `API_BASE_URL` | `http://localhost:8000` | FastAPI backend URL. Update to Pi's IP when distributed. |
| `MODEL_PATH` | `models/face_model.pt` | Trained YOLO weights path. |
| `DB_PATH` | `xtreme_care.db` | SQLite database file. |

---

## Individual scripts

| Script | Purpose |
|---|---|
| `capture.py` | Webcam capture + augmentation |
| `train.py` | YOLOv8n fine-tuning |
| `recognize.py` | Live face detection (run standalone to test) |
| `hand_track.py` | MediaPipe hand landmark tracking |
| `verify.py` | `VerificationSession` — 30s intake window logic |
| `api_client.py` | REST client for FastAPI backend |
| `database.py` | SQLite helpers |
| `utils.py` | Drawing helpers, timestamps, session name |
| `config.py` | All constants — tune here |
| `main.py` | Full pipeline entry point |

---

## Raspberry Pi 5 Deployment

Same code runs unmodified. Only potential change:

```python
# config.py
WEBCAM_INDEX = 0   # Pi Camera Module 3 via libcamera maps to index 0
```

Install picamera2 for best Pi Camera performance:

```bash
sudo apt install python3-picamera2
```

Reduce resolution if CPU is saturated:

```python
FRAME_WIDTH  = 320
FRAME_HEIGHT = 240
```

---

## Database

`xtreme_care.db` is created automatically on first run.

| Table | Contents |
|---|---|
| `dose_logs` | One row per dose event — status, timestamps, delay |
| `verification_events` | One row per verification attempt — face/hand flags |

Query today's logs in Python:

```python
from database import get_today_logs
for row in get_today_logs():
    print(row)
```
