# train.py — YOLOv8 face model fine-tuning for XtremeCare
# Compatible with ultralytics >= 8.3.0 and Python 3.14

import os
import shutil
import random
import yaml
from pathlib import Path
from ultralytics import YOLO
from config import PATIENT_ID, DATA_DIR, MODEL_PATH

RAW_DIR       = os.path.join(DATA_DIR, PATIENT_ID, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, PATIENT_ID, "processed")

TRAIN_IMG_DIR = os.path.join(PROCESSED_DIR, "images", "train")
VAL_IMG_DIR   = os.path.join(PROCESSED_DIR, "images", "val")
TRAIN_LBL_DIR = os.path.join(PROCESSED_DIR, "labels", "train")
VAL_LBL_DIR   = os.path.join(PROCESSED_DIR, "labels", "val")

EPOCHS   = 50
IMG_SIZE = 320
BATCH    = 8
SPLIT    = 0.8   # 80 % train / 20 % val


def create_dirs():
    for d in [TRAIN_IMG_DIR, VAL_IMG_DIR, TRAIN_LBL_DIR, VAL_LBL_DIR]:
        os.makedirs(d, exist_ok=True)


def get_images() -> list[str]:
    """Return sorted list of image paths in RAW_DIR."""
    supported = {".jpg", ".jpeg", ".png"}
    return [
        os.path.join(RAW_DIR, f)
        for f in sorted(os.listdir(RAW_DIR))
        if Path(f).suffix.lower() in supported
    ]


def write_label(label_path: str):
    """
    YOLO label for a face-centred full-frame capture.
    class_id  cx   cy   w    h   (all normalised 0-1)
    """
    with open(label_path, "w") as f:
        f.write("0 0.5 0.5 1.0 1.0\n")


def create_dataset_yaml() -> str:
    yaml_path = os.path.join(PROCESSED_DIR, "dataset.yaml")
    data = {
        "path":  os.path.abspath(PROCESSED_DIR),
        "train": "images/train",
        "val":   "images/val",
        "nc":    1,
        "names": [PATIENT_ID],
    }
    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    print(f"[TRAIN] Dataset YAML written to {yaml_path}")
    return yaml_path


def prepare_dataset() -> str:
    create_dirs()
    images = get_images()

    if not images:
        raise FileNotFoundError(
            f"No images found in {RAW_DIR}. Run capture.py first."
        )

    print(f"[TRAIN] Found {len(images)} images in {RAW_DIR}")

    random.seed(42)
    random.shuffle(images)

    split_idx  = int(len(images) * SPLIT)
    train_imgs = images[:split_idx]
    val_imgs   = images[split_idx:]

    print(f"[TRAIN] Split — train: {len(train_imgs)}, val: {len(val_imgs)}")

    for img_path in train_imgs:
        fname = os.path.basename(img_path)
        stem  = Path(fname).stem
        shutil.copy(img_path, os.path.join(TRAIN_IMG_DIR, fname))
        write_label(os.path.join(TRAIN_LBL_DIR, f"{stem}.txt"))

    for img_path in val_imgs:
        fname = os.path.basename(img_path)
        stem  = Path(fname).stem
        shutil.copy(img_path, os.path.join(VAL_IMG_DIR, fname))
        write_label(os.path.join(VAL_LBL_DIR, f"{stem}.txt"))

    return create_dataset_yaml()


def _extract_map(results) -> tuple[str, str]:
    """
    Extract mAP scores from an ultralytics Results object.
    Handles both the pre-8.2 dict API and the post-8.2 validator/metrics API.
    Returns (map50_str, map5095_str).
    """
    # ultralytics >= 8.2: results is a dict-like with direct metric keys
    try:
        m = results.results_dict
        map50   = m.get("metrics/mAP50(B)",    m.get("metrics/mAP50",   "N/A"))
        map5095 = m.get("metrics/mAP50-95(B)", m.get("metrics/mAP50-95", "N/A"))
        if map50 != "N/A":
            return str(round(float(map50), 4)), str(round(float(map5095), 4))
    except Exception:
        pass

    # ultralytics >= 8.3: metrics live on results.box
    try:
        box = results.box
        return str(round(float(box.map50), 4)), str(round(float(box.map), 4))
    except Exception:
        pass

    # Last resort: iterate over the results object as a dict
    try:
        metrics = dict(results)
        for k50, k95 in [
            ("mAP50", "mAP50-95"),
            ("map50", "map50-95"),
            ("metrics/mAP50(B)", "metrics/mAP50-95(B)"),
        ]:
            if k50 in metrics:
                return str(round(float(metrics[k50]), 4)), str(round(float(metrics.get(k95, 0)), 4))
    except Exception:
        pass

    return "N/A", "N/A"


def train_model(yaml_path: str):
    print("[TRAIN] Loading YOLOv8n base model...")
    model = YOLO("yolov8n.pt")   # auto-downloads if not cached

    print(f"[TRAIN] Starting training — {EPOCHS} epochs, imgsz={IMG_SIZE}, batch={BATCH}")
    print("[TRAIN] Training on CPU — expect 30-45 minutes. Don't close the window.")

    # Use absolute project path so ultralytics saves weights in our directory
    project_dir = Path(__file__).resolve().parent / "runs" / "detect"

    results = model.train(
        data=yaml_path,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH,
        name="xtreme_care_face",
        project=str(project_dir),
        device="cpu",
        verbose=True,
        exist_ok=True,
    )

    # Locate best weights — check the expected path first, then search
    best_weights = project_dir / "xtreme_care_face" / "weights" / "best.pt"
    if not best_weights.exists():
        # Search in the project dir and also 2 levels up (ultralytics quirk)
        search_roots = [project_dir, Path(__file__).resolve().parent]
        candidates = []
        for root in search_roots:
            candidates.extend(root.rglob("best.pt"))
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            print("[TRAIN] WARNING: Could not locate best.pt — check runs/detect/")
            return
        best_weights = candidates[0]
        print(f"[TRAIN] Found best.pt at: {best_weights}")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    shutil.copy(str(best_weights), MODEL_PATH)

    map50, map5095 = _extract_map(results)

    print(f"\n[TRAIN] Training complete.")
    print(f"[TRAIN] Best weights saved to : {MODEL_PATH}")
    print(f"[TRAIN] Final mAP@50          : {map50}")
    print(f"[TRAIN] Final mAP@50-95       : {map5095}")


if __name__ == "__main__":
    print("=" * 52)
    print("  XtremeCare — YOLOv8 Face Model Training")
    print("=" * 52)
    yaml_path = prepare_dataset()
    train_model(yaml_path)
    print("\n[TRAIN] Done. Run  python main.py  to start the pipeline.")
