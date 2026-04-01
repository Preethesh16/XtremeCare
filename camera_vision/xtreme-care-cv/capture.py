# capture.py — Patient face registration capture for XtremeCare
# Compatible with opencv >= 4.10, Pillow >= 11.0, numpy >= 2.0, Python 3.14

import cv2
import os
import time
import numpy as np
from PIL import Image, ImageEnhance
from config import WEBCAM_INDEX, FRAME_WIDTH, FRAME_HEIGHT, PATIENT_ID, DATA_DIR

TOTAL_PHOTOS     = 30
CAPTURE_INTERVAL = 1.0   # seconds between auto-captures

RAW_DIR = os.path.join(DATA_DIR, PATIENT_ID, "raw")


def _bgr_to_pil(img_bgr: np.ndarray) -> Image.Image:
    """Convert an OpenCV BGR ndarray to a Pillow RGB Image."""
    return Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))


def _pil_to_bgr(pil_img: Image.Image) -> np.ndarray:
    """Convert a Pillow RGB Image back to an OpenCV BGR ndarray."""
    return cv2.cvtColor(np.asarray(pil_img, dtype=np.uint8), cv2.COLOR_RGB2BGR)


def augment_image(img_bgr: np.ndarray,
                  base_name: str) -> list[tuple[str, np.ndarray]]:
    """
    Produce 4 augmented variants for every original capture:
      _flip   — horizontal mirror
      _bright — brightness +15 %
      _dark   — brightness -15 %
      _blur   — slight Gaussian blur

    Returns a list of (filename, bgr_image) tuples.
    """
    variants: list[tuple[str, np.ndarray]] = []

    # 1. Horizontal flip
    variants.append((f"{base_name}_flip.jpg", cv2.flip(img_bgr, 1)))

    # 2 & 3. Brightness via Pillow ImageEnhance
    pil_img  = _bgr_to_pil(img_bgr)
    enhancer = ImageEnhance.Brightness(pil_img)
    variants.append((f"{base_name}_bright.jpg", _pil_to_bgr(enhancer.enhance(1.15))))
    variants.append((f"{base_name}_dark.jpg",   _pil_to_bgr(enhancer.enhance(0.85))))

    # 4. Gaussian blur
    variants.append((f"{base_name}_blur.jpg",
                     cv2.GaussianBlur(img_bgr, (3, 3), 0)))

    return variants


def run_capture():
    os.makedirs(RAW_DIR, exist_ok=True)

    cap = cv2.VideoCapture(WEBCAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print(f"[ERROR] Cannot open webcam at index {WEBCAM_INDEX}.")
        print("        Change WEBCAM_INDEX in config.py if you have multiple cameras.")
        return

    captured         = 0
    total_saved      = 0
    last_capture_ts  = 0.0
    cx, cy           = FRAME_WIDTH // 2, FRAME_HEIGHT // 2
    box_w, box_h     = 200, 260

    print(f"[CAPTURE] Starting face registration for {PATIENT_ID}")
    print(f"[CAPTURE] Capturing {TOTAL_PHOTOS} photos → {RAW_DIR}")
    print("[CAPTURE] Press Q to quit early.")

    while captured < TOTAL_PHOTOS:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read from webcam.")
            break

        display = frame.copy()

        # Instruction
        cv2.putText(display,
                    "Look straight at camera. Keep face centred.",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 2, cv2.LINE_AA)

        # Progress
        cv2.putText(display, f"Captured: {captured}/{TOTAL_PHOTOS}",
                    (10, FRAME_HEIGHT - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

        # Countdown to next capture
        elapsed_since = time.time() - last_capture_ts
        remaining     = max(0.0, CAPTURE_INTERVAL - elapsed_since)
        cv2.putText(display, f"Next in: {remaining:.1f}s",
                    (FRAME_WIDTH - 180, FRAME_HEIGHT - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2, cv2.LINE_AA)

        # Face guide box
        cv2.rectangle(display,
                      (cx - box_w // 2, cy - box_h // 2),
                      (cx + box_w // 2, cy + box_h // 2),
                      (0, 255, 255), 2)

        cv2.imshow("XtremeCare — Face Capture", display)

        # Auto-capture on interval
        if time.time() - last_capture_ts >= CAPTURE_INTERVAL:
            captured     += 1
            base_name    = f"{PATIENT_ID}_{captured:03d}"
            orig_path    = os.path.join(RAW_DIR, f"{base_name}.jpg")
            cv2.imwrite(orig_path, frame)
            total_saved  += 1

            for aug_name, aug_img in augment_image(frame, base_name):
                cv2.imwrite(os.path.join(RAW_DIR, aug_name), aug_img)
                total_saved += 1

            print(f"[CAPTURE] {captured}/{TOTAL_PHOTOS} — {base_name} + 4 augmented")
            last_capture_ts = time.time()

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q')):
            print("[CAPTURE] Quit early by user.")
            break

    cap.release()
    cv2.destroyAllWindows()

    print(f"\n[CAPTURE] Complete. {total_saved} images saved to {RAW_DIR}")
    print("[CAPTURE] Next step: python train.py")


if __name__ == "__main__":
    run_capture()
