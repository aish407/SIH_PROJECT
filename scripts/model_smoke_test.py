"""Run the deployed RoadWatch models against stored uploaded-road video frames.

This is a smoke test: it proves each production checkpoint can load and run.
It does not claim a model is accurate unless the sampled footage contains its class.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
VIDEO_DIR = ROOT / "outputs" / "pothole_videos"
REPORT_PATH = ROOT / "outputs" / "model_smoke_test_report.json"
MODELS = {
    "general_objects": ROOT / "yolo26n.pt",
    "road_damage": ROOT / "models" / "YOLOv8_Small_RDD.pt",
    "waterlogging": ROOT / "models" / "waterlogging" / "best.pt",
    "speedbreaker": ROOT / "models" / "speedbreaker" / "speedbreaker_best.pt",
    "zebra_crossing": ROOT / "models" / "zebra_crossing" / "best.pt",
    "road_divider": ROOT / "models" / "road_divider" / "divider.pt",
    "accident": ROOT / "models" / "accident" / "model.pt",
    "license_plate": ROOT / "models" / "lincense_plate" / "best.pt",
}


def sample_frames() -> list[tuple[str, object]]:
    videos = sorted(VIDEO_DIR.glob("*_source.mp4"), key=lambda item: item.stat().st_size, reverse=True)[:3]
    samples: list[tuple[str, object]] = []
    for video in videos:
        capture = cv2.VideoCapture(str(video))
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        for position in (0.2, 0.5, 0.8):
            capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(total * position)))
            ok, frame = capture.read()
            if ok:
                samples.append((video.name, frame))
        capture.release()
    return samples


def main() -> None:
    frames = sample_frames()
    if not frames:
        raise SystemExit("No uploaded source videos found in outputs/pothole_videos")
    report: dict[str, object] = {"frames_tested": len(frames), "models": {}}
    for name, path in MODELS.items():
        entry: dict[str, object] = {"checkpoint": str(path.relative_to(ROOT)), "loaded": False, "classes": {}, "detections": 0, "max_confidence": 0.0, "error": None}
        try:
            model = YOLO(str(path))
            entry["loaded"] = True
            entry["classes"] = {str(key): value for key, value in model.names.items()}
            for _, frame in frames:
                result = model(frame, conf=0.25, imgsz=512, verbose=False)[0]
                if result.boxes is None:
                    continue
                scores = [float(score) for score in result.boxes.conf]
                entry["detections"] = int(entry["detections"]) + len(scores)
                if scores:
                    entry["max_confidence"] = max(float(entry["max_confidence"]), max(scores))
        except Exception as error:  # Report rather than hiding model compatibility failures.
            entry["error"] = f"{type(error).__name__}: {error}"
        report["models"][name] = entry
        print(f"{name}: loaded={entry['loaded']}, detections={entry['detections']}, error={entry['error']}")
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
