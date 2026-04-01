# recognize.py — Live face recognition using trained YOLOv8 model
# Compatible with ultralytics >= 8.3.0, numpy >= 2.0, Python 3.14
#
# Two-stage detection:
#   1. MediaPipe FaceLandmarker checks if ANY real human face exists
#   2. Only then YOLO checks if it's the registered patient
# This prevents false positives on empty rooms / objects.

import os
import cv2
import numpy as np
from ultralytics import YOLO

try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core.base_options import BaseOptions
    _MP_AVAILABLE = True
except ImportError:
    _MP_AVAILABLE = False

from config import (
    MODEL_PATH, FACE_CONFIDENCE_THRESHOLD, FACE_LANDMARKER_PATH,
    WEBCAM_INDEX, FRAME_WIDTH, FRAME_HEIGHT, PATIENT_NAME,
)
from utils import draw_face_box

_model: YOLO | None = None
_face_detector = None


def _load_model() -> YOLO:
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at '{MODEL_PATH}'. "
                "Run  python train.py  first."
            )
        _model = YOLO(MODEL_PATH)
        print(f"[RECOGNIZE] YOLO model loaded from {MODEL_PATH}")
    return _model


def _get_face_detector():
    """Load MediaPipe FaceLandmarker to verify a real face exists."""
    global _face_detector
    if not _MP_AVAILABLE:
        return None
    if _face_detector is None:
        if not os.path.exists(FACE_LANDMARKER_PATH):
            print(f"[RECOGNIZE] WARNING: {FACE_LANDMARKER_PATH} not found. "
                  "Face-presence gate disabled.")
            return None
        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=FACE_LANDMARKER_PATH),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
        )
        _face_detector = vision.FaceLandmarker.create_from_options(options)
        print("[RECOGNIZE] MediaPipe face-presence gate loaded.")
    return _face_detector


def _real_face_present(frame: np.ndarray) -> bool:
    """
    Use MediaPipe FaceLandmarker to check if an actual human face
    is in the frame. Returns True only if a real face is detected.
    This prevents the YOLO model from false-detecting walls/objects.
    """
    detector = _get_face_detector()
    if detector is None:
        # If MediaPipe is unavailable, skip the gate (fallback to YOLO only)
        return True

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = detector.detect(mp_image)

    return len(result.face_landmarks) > 0


def detect_patient(frame: np.ndarray) -> tuple[bool, float, tuple | None]:
    """
    Run face detection on a single BGR frame.

    Two-stage process:
      1. MediaPipe checks if a real human face exists in the frame
      2. YOLO checks if that face belongs to the registered patient

    Returns:
        detected   (bool)  — True when real face found AND YOLO confidence >= threshold
        confidence (float) — YOLO confidence (0.0 if no face or no detection)
        bbox       (tuple) — (x1, y1, x2, y2) pixel ints, or None
    """
    # Stage 1: Is there a real human face at all?
    if not _real_face_present(frame):
        return False, 0.0, None

    # Stage 2: Is it the registered patient?
    model   = _load_model()
    results = model.predict(frame, verbose=False)

    best_conf = 0.0
    best_bbox: tuple | None = None

    for result in results:
        if result.boxes is None or len(result.boxes) == 0:
            continue
        for box in result.boxes:
            conf = float(box.conf[0])
            if conf > best_conf:
                best_conf = conf
                xyxy      = box.xyxy[0].tolist()
                best_bbox = tuple(int(v) for v in xyxy)

    if best_conf >= FACE_CONFIDENCE_THRESHOLD and best_bbox is not None:
        label = f"{PATIENT_NAME} — {best_conf * 100:.0f}%"
        draw_face_box(frame, best_bbox, label, color=(0, 220, 0))
        return True, best_conf, best_bbox

    if best_bbox is not None:
        label = f"Unknown — {best_conf * 100:.0f}%"
        draw_face_box(frame, best_bbox, label, color=(0, 0, 220))

    return False, best_conf, None


def run_live_detection():
    """Standalone webcam loop — shows live face detection. Press Q to quit."""
    cap = cv2.VideoCapture(WEBCAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print(f"[ERROR] Cannot open webcam at index {WEBCAM_INDEX}.")
        return

    print("[RECOGNIZE] Live detection running. Press Q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Frame read failed.")
            break

        detected, conf, _ = detect_patient(frame)

        status_text  = "PATIENT DETECTED" if detected else "NO MATCH"
        status_color = (0, 220, 0) if detected else (0, 0, 220)
        cv2.putText(frame, status_text,
                    (10, FRAME_HEIGHT - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    status_color, 2, cv2.LINE_AA)

        cv2.imshow("XtremeCare — Face Recognition", frame)
        if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q')):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_live_detection()
