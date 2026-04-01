# hand_track.py — MediaPipe hand landmark tracking for XtremeCare
# Uses the new mediapipe Tasks API (>= 0.10.21) — mp.solutions is removed.
# Python 3.14 compatible.

import os
import cv2
import numpy as np

try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core.base_options import BaseOptions
    from mediapipe.tasks.python.vision import drawing_utils as mp_drawing
    from mediapipe.tasks.python.vision import HandLandmarksConnections

    _MP_AVAILABLE = True
except ImportError:
    _MP_AVAILABLE = False
    print("[hand_track] WARNING: mediapipe not installed. Hand tracking disabled.")

from config import HAND_LANDMARKER_PATH

# Fingertip landmark indices: thumb=4, index=8, middle=12, ring=16, pinky=20
FINGERTIP_IDS = [4, 8, 12, 16, 20]

_hand_landmarker = None


def _get_hand_landmarker():
    """Return a shared HandLandmarker instance (lazy init)."""
    global _hand_landmarker
    if not _MP_AVAILABLE:
        return None
    if _hand_landmarker is None:
        if not os.path.exists(HAND_LANDMARKER_PATH):
            print(f"[hand_track] ERROR: Model file not found: {HAND_LANDMARKER_PATH}")
            print("             Download it from: https://storage.googleapis.com/mediapipe-models/"
                  "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task")
            return None

        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=HAND_LANDMARKER_PATH),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        _hand_landmarker = vision.HandLandmarker.create_from_options(options)
        print("[hand_track] HandLandmarker initialised.")
    return _hand_landmarker


def get_hand_landmarks(frame: np.ndarray):
    """
    Detect a hand in the BGR frame.

    Returns:
        list[NormalizedLandmark] (21 landmarks) if a hand is found, else None.
    Draws landmarks onto frame in-place.
    """
    if not _MP_AVAILABLE:
        return None

    landmarker = _get_hand_landmarker()
    if landmarker is None:
        return None

    # Convert BGR → RGB and wrap in mediapipe Image
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = landmarker.detect(mp_image)

    if not result.hand_landmarks:
        return None

    # First hand's 21 landmarks
    landmarks = result.hand_landmarks[0]

    # Draw landmarks onto the original BGR frame
    mp_drawing.draw_landmarks(
        frame,
        landmarks,
        HandLandmarksConnections.HAND_CONNECTIONS,
        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
        mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=1),
    )

    return landmarks


def get_wrist_position(landmarks, frame_shape: tuple) -> tuple[float, float]:
    """
    Return normalised (x, y) of the wrist (landmark index 0).
    Coordinates are 0.0–1.0 relative to frame size.
    """
    wrist = landmarks[0]
    return (wrist.x, wrist.y)


def get_fingertip_positions(landmarks,
                             frame_shape: tuple) -> list[tuple[float, float]]:
    """
    Return normalised (x, y) for all 5 fingertips.
    Order: thumb, index, middle, ring, pinky.
    """
    return [(landmarks[tid].x, landmarks[tid].y) for tid in FINGERTIP_IDS]
