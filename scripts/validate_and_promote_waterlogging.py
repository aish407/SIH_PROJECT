"""Validate the trained road-water detector and promote only a usable checkpoint."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "waterlogging_roboflow_v2" / "data.yaml"
BEST = ROOT / "runs" / "waterlogging_v2" / "weights" / "best.pt"
TARGET = ROOT / "models" / "waterlogging" / "roadwater_v2_best.pt"
REPORT = ROOT / "outputs" / "waterlogging_v2_validation.json"


def main() -> None:
    if not BEST.exists():
        raise FileNotFoundError(f"Training checkpoint not found: {BEST}")
    metrics = YOLO(str(BEST)).val(
        data=str(DATA),
        split="test",
        imgsz=640,
        batch=1,
        workers=0,
        device="cpu",
        project=str(ROOT / "runs"),
        name="waterlogging_v2_test",
        exist_ok=True,
    )
    report = {
        "checkpoint": str(BEST.relative_to(ROOT)),
        "precision": round(float(metrics.box.mp), 4),
        "recall": round(float(metrics.box.mr), 4),
        "map50": round(float(metrics.box.map50), 4),
        "map50_95": round(float(metrics.box.map), 4),
        "promotion_threshold_map50": 0.35,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if report["map50"] < report["promotion_threshold_map50"]:
        raise RuntimeError(f"Not promoting weak checkpoint: {report}")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BEST, TARGET)
    print(json.dumps({**report, "promoted_to": str(TARGET.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
