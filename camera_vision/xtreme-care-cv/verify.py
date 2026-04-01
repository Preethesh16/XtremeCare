# verify.py — Hand-to-mouth intake verification logic for XtremeCare
# Uses the new mediapipe Tasks API (>= 0.10.21) — mp.solutions is removed.
# Python 3.14 compatible.

import os
import time
import cv2
import numpy as np

try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core.base_options import BaseOptions

    _MP_AVAILABLE = True
except ImportError:
    _MP_AVAILABLE = False
    print("[verify] WARNING: mediapipe not installed. Mouth detection disabled.")

from config import (
    MOUTH_DISTANCE_THRESHOLD,
    VERIFICATION_WINDOW_SECONDS,
    FACE_LANDMARKER_PATH,
)
from recognize import detect_patient
from hand_track import get_hand_landmarks, get_wrist_position

# MediaPipe Face Mesh landmark 13 = upper lip centre
UPPER_LIP_LANDMARK = 13

_face_landmarker = None


def _get_face_landmarker():
    """Return a shared FaceLandmarker instance (lazy init)."""
    global _face_landmarker
    if not _MP_AVAILABLE:
        return None
    if _face_landmarker is None:
        if not os.path.exists(FACE_LANDMARKER_PATH):
            print(f"[verify] ERROR: Model file not found: {FACE_LANDMARKER_PATH}")
            print("         Download it from: https://storage.googleapis.com/mediapipe-models/"
                  "face_landmarker/face_landmarker/float16/latest/face_landmarker.task")
            return None

        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=FACE_LANDMARKER_PATH),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        _face_landmarker = vision.FaceLandmarker.create_from_options(options)
        print("[verify] FaceLandmarker initialised.")
    return _face_landmarker


def get_mouth_position(frame: np.ndarray) -> tuple[float, float] | None:
    """
    Detect the upper-lip centre using MediaPipe FaceLandmarker.
    Returns normalised (x, y) in 0.0–1.0, or None if no face / no mediapipe.
    """
    landmarker = _get_face_landmarker()
    if landmarker is None:
        return None

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = landmarker.detect(mp_image)

    if not result.face_landmarks:
        return None

    lip = result.face_landmarks[0][UPPER_LIP_LANDMARK]
    return (lip.x, lip.y)


def calculate_distance(point1: tuple[float, float],
                        point2: tuple[float, float]) -> float:
    """Euclidean distance between two normalised (x, y) pairs."""
    dx = point1[0] - point2[0]
    dy = point1[1] - point2[1]
    return (dx * dx + dy * dy) ** 0.5


def is_hand_near_mouth(wrist_pos: tuple[float, float],
                        mouth_pos: tuple[float, float]) -> bool:
    """True when wrist is within MOUTH_DISTANCE_THRESHOLD of mouth."""
    return calculate_distance(wrist_pos, mouth_pos) < MOUTH_DISTANCE_THRESHOLD


class VerificationSession:
    """
    Manages one dose-verification window.

    Call update(frame) every frame. Returns:
        PENDING   — still waiting
        VERIFIED  — face confirmed + hand near mouth detected
        MISSED    — window elapsed without intake gesture
    """

    STATUS_PENDING  = "PENDING"
    STATUS_VERIFIED = "VERIFIED"
    STATUS_MISSED   = "MISSED"

    def __init__(self, session_name: str):
        self.session_name    = session_name
        self.start_time      = time.time()
        self.face_confirmed  = False
        self.hand_detected   = False
        self._status         = self.STATUS_PENDING
        self._complete       = False
        print(f"[VERIFY] Session started: {session_name} — "
              f"{VERIFICATION_WINDOW_SECONDS}s window")

    def update(self, frame: np.ndarray) -> str:
        """Process one frame. Mutates frame with overlays. Returns status."""
        if self._complete:
            return self._status

        elapsed   = time.time() - self.start_time
        remaining = max(0.0, VERIFICATION_WINDOW_SECONDS - elapsed)

        # Countdown — top centre
        h, w = frame.shape[:2]
        cv2.putText(frame, f"Time: {remaining:.0f}s",
                    (w // 2 - 50, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 200, 255), 2, cv2.LINE_AA)

        # Stage 1 — face detection (YOLO)
        face_ok, _conf, _bbox = detect_patient(frame)
        if face_ok:
            self.face_confirmed = True

        # Stage 2 — hand + mouth only after face confirmed
        if self.face_confirmed:
            mouth_pos = get_mouth_position(frame)
            landmarks = get_hand_landmarks(frame)

            if landmarks is not None:
                self.hand_detected = True
                wrist_pos = get_wrist_position(landmarks, frame.shape)

                if mouth_pos is not None:
                    # Draw mouth position dot
                    mx = int(mouth_pos[0] * w)
                    my = int(mouth_pos[1] * h)
                    cv2.circle(frame, (mx, my), 8, (0, 165, 255), -1)

                    if is_hand_near_mouth(wrist_pos, mouth_pos):
                        self._status   = self.STATUS_VERIFIED
                        self._complete = True
                        print("[VERIFY] VERIFIED — hand near mouth detected.")
                        return self._status

        # Timeout check
        if elapsed >= VERIFICATION_WINDOW_SECONDS:
            self._status   = self.STATUS_MISSED
            self._complete = True
            print("[VERIFY] MISSED — verification window expired.")
            return self._status

        return self.STATUS_PENDING

    def is_complete(self) -> bool:
        return self._complete

    @property
    def status(self) -> str:
        return self._status
