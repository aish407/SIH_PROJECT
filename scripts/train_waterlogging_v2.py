"""Train the project waterlogging detector from the checked-in Roboflow export.

This is intentionally a small, CPU-safe fine-tuning configuration. The new
weights are written separately, so the currently deployed legacy model is not
replaced until validation succeeds.
"""

from __future__ import annotations

import os
from pathlib import Path

import torch
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "waterlogging_roboflow_v2" / "data.yaml"
BASE_MODEL = ROOT / "yolo26n.pt"
RUNS = ROOT / "runs"


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(f"Dataset configuration not found: {DATA}")
    if not BASE_MODEL.exists():
        raise FileNotFoundError(f"Base model not found: {BASE_MODEL}")

    # Keep Ultralytics state in this project so training is reproducible.
    os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".ultralytics-config"))
    device = 0 if torch.cuda.is_available() else "cpu"
    model = YOLO(str(BASE_MODEL))
    model.train(
        data=str(DATA),
        epochs=30,
        imgsz=416,
        batch=8 if device == "cpu" else 4,
        device=device,
        workers=0,
        cache=False,
        patience=10,
        optimizer="AdamW",
        lr0=0.001,
        cos_lr=True,
        mosaic=0.4,
        mixup=0.05,
        project=str(RUNS),
        name="waterlogging_v2",
        exist_ok=True,
        pretrained=True,
        verbose=True,
        seed=42,
    )


if __name__ == "__main__":
    main()
