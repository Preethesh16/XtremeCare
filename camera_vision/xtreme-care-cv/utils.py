# utils.py — helper functions for XtremeCare CV pipeline
# Python 3.14, numpy >= 2.0, mediapipe >= 0.10.21 (Tasks API)

from datetime import datetime
import cv2
import numpy as np


def get_timestamp() -> str:
    """Return current time as ISO 8601 string."""
    return datetime.now().isoformat(timespec="seconds")


def get_session_from_time() -> str:
    """
    Return MORNING / AFTERNOON / NIGHT based on current hour.
      Morning:   06:00 – 11:59
      Afternoon: 12:00 – 17:59
      Night:     18:00 – 23:59
    """
    hour = datetime.now().hour
    if 6 <= hour <= 11:
        return "MORNING"
    elif 12 <= hour <= 17:
        return "AFTERNOON"
    elif 18 <= hour <= 23:
        return "NIGHT"
    else:
        return "MORNING"


def draw_face_box(frame: np.ndarray, bbox: tuple,
                  label: str, color: tuple) -> np.ndarray:
    """
    Draw a bounding box with a filled label bar on frame.

    Args:
        bbox:  (x1, y1, x2, y2) pixel coordinates
        label: text to show
        color: BGR tuple e.g. (0, 255, 0)
    """
    x1, y1, x2, y2 = (int(v) for v in bbox)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), baseline = cv2.getTextSize(label, font, 0.6, 2)

    cv2.rectangle(frame,
                  (x1, y1 - th - baseline - 4),
                  (x1 + tw + 4, y1),
                  color, cv2.FILLED)
    cv2.putText(frame, label,
                (x1 + 2, y1 - baseline - 2),
                font, 0.6, (0, 0, 0), 2)
    return frame


def draw_landmarks(frame: np.ndarray, landmarks) -> np.ndarray:
    """
    Draw hand landmarks on frame using the new mediapipe Tasks API.

    landmarks: list[NormalizedLandmark] from HandLandmarkerResult.hand_landmarks[0]
    """
    try:
        from mediapipe.tasks.python.vision import drawing_utils as mp_drawing
        from mediapipe.tasks.python.vision import HandLandmarksConnections

        mp_drawing.draw_landmarks(
            frame,
            landmarks,
            HandLandmarksConnections.HAND_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
            mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=1),
        )
    except ImportError:
        # Fallback: just draw dots manually if mediapipe isn't available
        h, w = frame.shape[:2]
        for lm in landmarks:
            px = int(lm.x * w)
            py = int(lm.y * h)
            cv2.circle(frame, (px, py), 3, (0, 255, 0), -1)

    return frame


def draw_status_overlay(frame: np.ndarray, text: str,
                        color: tuple) -> np.ndarray:
    """
    Draw large status text centred at the bottom of the frame
    over a semi-transparent black strip.
    """
    h, w   = frame.shape[:2]
    font   = cv2.FONT_HERSHEY_SIMPLEX
    scale  = 1.0
    thick  = 2

    (tw, th), baseline = cv2.getTextSize(text, font, scale, thick)
    x = (w - tw) // 2
    y = h - 20

    overlay = frame.copy()
    cv2.rectangle(overlay,
                  (0, y - th - baseline - 8),
                  (w, h),
                  (0, 0, 0), cv2.FILLED)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    cv2.putText(frame, text, (x, y), font, scale, color, thick, cv2.LINE_AA)
    return frame


def resize_frame(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """
    Resize frame to (width x height) maintaining aspect ratio.
    Black letterbox/pillarbox bars fill the remainder.
    """
    h, w = frame.shape[:2]
    target_ratio = width / height
    src_ratio    = w / h

    if abs(src_ratio - target_ratio) < 0.01:
        return cv2.resize(frame, (width, height))

    if src_ratio > target_ratio:
        new_w = width
        new_h = int(width / src_ratio)
    else:
        new_h = height
        new_w = int(height * src_ratio)

    resized = cv2.resize(frame, (new_w, new_h))
    canvas  = np.zeros((height, width, 3), dtype=np.uint8)
    x_off   = (width  - new_w) // 2
    y_off   = (height - new_h) // 2
    canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
    return canvas
