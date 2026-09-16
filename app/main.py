"""Local road-safety detection dashboard powered by Ultralytics YOLO and Supervision."""

from __future__ import annotations

import base64
import json
from concurrent.futures import ThreadPoolExecutor
import os
import shutil
import sqlite3
import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import supervision as sv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as PdfImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "app" / "static"
MODEL_PATH = ROOT / "yolo26n.pt"
ROAD_DAMAGE_MODEL_PATH = ROOT / "models" / "YOLOv8_Small_RDD.pt"
# Keep the legacy checkpoint as a fallback. A validation-approved, locally
# trained checkpoint is preferred automatically after it is written here.
WATERLOGGING_LEGACY_MODEL_PATH = ROOT / "models" / "waterlogging" / "best.pt"
WATERLOGGING_CANDIDATE_MODEL_PATH = ROOT / "models" / "waterlogging" / "roadwater_v2_best.pt"
WATERLOGGING_MODEL_PATH = (
    WATERLOGGING_CANDIDATE_MODEL_PATH
    if WATERLOGGING_CANDIDATE_MODEL_PATH.exists()
    else WATERLOGGING_LEGACY_MODEL_PATH
)
SPEEDBREAKER_MODEL_PATH = ROOT / "models" / "speedbreaker" / "speedbreaker_best.pt"
ZEBRA_CROSSING_MODEL_PATH = ROOT / "models" / "zebra_crossing" / "best.pt"
ROAD_DIVIDER_MODEL_PATH = ROOT / "models" / "road_divider" / "divider.pt"
ACCIDENT_MODEL_PATH = ROOT / "models" / "accident" / "model.pt"
# Current verified license-plate checkpoint supplied by the user.
PLATE_MODEL_PATH = ROOT / "models" / "lincense_plate" / "best.pt"
PYRESEARCH_POTHOLE_MODEL_PATH = ROOT / "models" / "pyresearch_pothole_best.pt"
POTHOLE_VIDEO_MODEL_PATH = ROAD_DAMAGE_MODEL_PATH
VIDEO_DIR = ROOT / "outputs" / "pothole_videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
ACCIDENT_EVIDENCE_DIR = ROOT / "outputs" / "accident_evidence"
ACCIDENT_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR = ROOT / "outputs" / "pdf"
PDF_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = ROOT / "outputs" / "roadwatch.db"
ROAD_DAMAGE_INTERVAL_SECONDS = 3.0
ROAD_DAMAGE_CONFIDENCE = 0.65
# Ultralytics creates its own "Ultralytics" subfolder inside this configurable base path.
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT))

from ultralytics import YOLO

app = FastAPI(title="RoadWatch GIS", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

model: YOLO | None = None
road_damage_model: YOLO | None = None
waterlogging_model: YOLO | None = None
speedbreaker_model: YOLO | None = None
zebra_crossing_model: YOLO | None = None
road_divider_model: YOLO | None = None
pothole_model: YOLO | None = None
accident_model: YOLO | None = None
plate_model: YOLO | None = None
model_lock = threading.Lock()
road_model_lock = threading.Lock()
waterlogging_model_lock = threading.Lock()
speedbreaker_model_lock = threading.Lock()
zebra_crossing_model_lock = threading.Lock()
road_divider_model_lock = threading.Lock()
accident_model_lock = threading.Lock()
road_scan_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="road-damage")
db_lock = threading.Lock()
drivers: dict[str, dict[str, Any]] = {}
video_jobs: dict[str, dict[str, Any]] = {}
box_annotator = sv.BoxAnnotator(thickness=2)
label_annotator = sv.LabelAnnotator(text_scale=0.55, text_thickness=1)


class LocationUpdate(BaseModel):
    driver_id: str = Field(min_length=1, max_length=80)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0)


class DefectUpdate(BaseModel):
    status: str | None = None
    deadline: str | None = None


class BusCreate(BaseModel):
    """A government-maintained bus registry entry."""
    bus_number: str = Field(min_length=1, max_length=80)
    source: str = Field(min_length=1, max_length=160)
    destination: str = Field(min_length=1, max_length=160)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


def database() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with db_lock, database() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS infrastructure_defects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                defect_type TEXT NOT NULL,
                driver_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                confidence REAL NOT NULL,
                priority INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Detected',
                deadline TEXT,
                detected_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS traffic_analysis_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                cars INTEGER NOT NULL DEFAULT 0,
                bikes INTEGER NOT NULL DEFAULT 0,
                buses INTEGER NOT NULL DEFAULT 0,
                total_vehicles INTEGER NOT NULL DEFAULT 0,
                density TEXT NOT NULL DEFAULT 'Low',
                estimated_delay_minutes INTEGER NOT NULL DEFAULT 0,
                insight TEXT NOT NULL DEFAULT '',
                priority INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Detected',
                deadline TEXT,
                detected_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS accident_incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                confidence REAL NOT NULL,
                severity TEXT NOT NULL,
                plates_json TEXT NOT NULL,
                evidence_path TEXT,
                detected_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS buses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bus_number TEXT NOT NULL UNIQUE COLLATE NOCASE,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sidewalk_obstruction_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                vehicle_class TEXT NOT NULL,
                confidence REAL NOT NULL,
                side TEXT NOT NULL,
                stopped_seconds REAL NOT NULL,
                priority INTEGER NOT NULL,
                detected_at TEXT NOT NULL
            )
        """)
        # Keep existing local databases compatible when a dashboard is upgraded.
        existing_columns = {row[1] for row in connection.execute("PRAGMA table_info(traffic_analysis_events)")}
        for column, definition in {
            "density": "TEXT NOT NULL DEFAULT 'Low'",
            "estimated_delay_minutes": "INTEGER NOT NULL DEFAULT 0",
            "insight": "TEXT NOT NULL DEFAULT ''",
        }.items():
            if column not in existing_columns:
                connection.execute(f"ALTER TABLE traffic_analysis_events ADD COLUMN {column} {definition}")


initialize_database()


def now() -> str:
    return datetime.now(UTC).isoformat()


def get_model() -> YOLO:
    global model
    if model is None:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=500, detail=f"Model not found: {MODEL_PATH.name}")
        model = YOLO(str(MODEL_PATH))
    return model


def get_road_damage_model() -> YOLO:
    global road_damage_model
    if road_damage_model is None:
        if not ROAD_DAMAGE_MODEL_PATH.exists():
            raise HTTPException(status_code=500, detail=f"Road-damage model not found: {ROAD_DAMAGE_MODEL_PATH.name}")
        road_damage_model = YOLO(str(ROAD_DAMAGE_MODEL_PATH))
    return road_damage_model


def get_waterlogging_model() -> YOLO:
    """Load the selected waterlogging checkpoint once, independently of road damage."""
    global waterlogging_model
    if waterlogging_model is None:
        if not WATERLOGGING_MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail="Waterlogging model is missing: models/waterlogging/best.pt")
        waterlogging_model = YOLO(str(WATERLOGGING_MODEL_PATH))
    return waterlogging_model


def get_speedbreaker_model() -> YOLO:
    """Load the verified speedbreaker detector once and keep it separate from other road models."""
    global speedbreaker_model
    if speedbreaker_model is None:
        if not SPEEDBREAKER_MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail="Speedbreaker model is missing: models/speedbreaker/speedbreaker_best.pt")
        speedbreaker_model = YOLO(str(SPEEDBREAKER_MODEL_PATH))
    return speedbreaker_model


def get_zebra_crossing_model() -> YOLO:
    """Load the verified zebra-crossing detector without sharing the other road-model pipeline."""
    global zebra_crossing_model
    if zebra_crossing_model is None:
        if not ZEBRA_CROSSING_MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail="Zebra-crossing model is missing: models/zebra_crossing/best.pt")
        zebra_crossing_model = YOLO(str(ZEBRA_CROSSING_MODEL_PATH))
    return zebra_crossing_model


def get_road_divider_model() -> YOLO:
    """Load the divider-present model separately from all defect detectors."""
    global road_divider_model
    if road_divider_model is None:
        if not ROAD_DIVIDER_MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail="Road-divider model is missing: models/road_divider/divider.pt")
        road_divider_model = YOLO(str(ROAD_DIVIDER_MODEL_PATH))
    return road_divider_model


def get_accident_model() -> YOLO:
    global accident_model
    if accident_model is None:
        if not ACCIDENT_MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail="Accident model is missing: models/accident/model.pt")
        accident_model = YOLO(str(ACCIDENT_MODEL_PATH))
    return accident_model


def get_plate_model() -> YOLO:
    global plate_model
    if plate_model is None:
        if not PLATE_MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail="License-plate model is missing: models/lincense_plate/best.pt")
        plate_model = YOLO(str(PLATE_MODEL_PATH))
    return plate_model


def get_pothole_model() -> YOLO:
    """Load the tested compatible pothole detector once for all uploaded-video jobs."""
    global pothole_model
    if pothole_model is None:
        if not POTHOLE_VIDEO_MODEL_PATH.exists():
            raise HTTPException(
                status_code=503,
                detail=f"Compatible pothole model is missing: {POTHOLE_VIDEO_MODEL_PATH.relative_to(ROOT)}",
            )
        # PyResearch's best.pt uses an older AAttn.qkv layer and is incompatible with current Ultralytics.
        # Use the already-installed RDD YOLOv8 model, constrained to the Potholes class, instead.
        pothole_model = YOLO(str(POTHOLE_VIDEO_MODEL_PATH))
    return pothole_model


def state(driver_id: str) -> dict[str, Any]:
    return drivers.setdefault(
        driver_id,
        {"driver_id": driver_id, "latitude": None, "longitude": None, "accuracy_m": None,
         "last_seen": None, "detections": [], "last_frame": None, "scans": 0,
         "analysis": {"density": "Unknown", "vehicle_count": 0, "person_count": 0, "alerts": []},
         "road_damage": {"status": "Waiting for road scan", "count": 0, "counts": {}, "detections": [], "last_scanned": None},
         "waterlogging": {"status": "Waiting for waterlogging scan", "count": 0, "detections": [], "last_scanned": None},
         "speedbreakers": {"status": "Waiting for speedbreaker scan", "count": 0, "detections": [], "last_scanned": None},
         "zebra_crossings": {"status": "Waiting for zebra-crossing scan", "count": 0, "detections": [], "last_scanned": None},
         "road_dividers": {"status": "Waiting for road-divider scan", "count": 0, "detections": [], "last_scanned": None},
         "sidewalk_obstructions": {"status": "Configure a sidewalk zone to begin", "count": 0, "detections": [], "last_scanned": None},
         "next_road_scan": 0.0, "road_scan_pending": False},
    )


def ensure_bus_record(bus_number: str) -> None:
    """Register a driver camera as an unconfigured bus without overwriting official route data."""
    cleaned = bus_number.strip()
    if not cleaned:
        return
    with db_lock, database() as connection:
        connection.execute(
            """INSERT OR IGNORE INTO buses (bus_number, source, destination, latitude, longitude, created_at, updated_at)
               VALUES (?, 'Route not configured', 'Route not configured', NULL, NULL, ?, ?)""",
            (cleaned, now(), now()),
        )


def encode_jpeg(frame: np.ndarray) -> str:
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
    if not ok:
        raise HTTPException(status_code=500, detail="Could not encode annotated frame")
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode("ascii")


def device_details() -> dict[str, str | bool]:
    import torch

    cuda = torch.cuda.is_available()
    return {"device": "CUDA" if cuda else "CPU", "fp16": cuda}


def scan_road_damage(driver_id: str, frame: np.ndarray) -> None:
    """Low-priority road scan that never blocks the primary live-object response."""
    record = state(driver_id)
    try:
        import torch

        # A stricter threshold removes the weak water/shadow false positives visible in the previous feed.
        with torch.inference_mode():
            result = get_road_damage_model()(frame, conf=ROAD_DAMAGE_CONFIDENCE, imgsz=512, verbose=False)[0]
        damage_items = []
        damage_counts: dict[str, int] = {}
        for class_id, score, box in zip(result.boxes.cls, result.boxes.conf, result.boxes.xyxy):
            label = result.names[int(class_id)]
            damage_counts[label] = damage_counts.get(label, 0) + 1
            damage_items.append({"class": label, "confidence": round(float(score), 4),
                                 "box": [round(float(value), 1) for value in box]})
        record["road_damage"] = {
            "status": "Damage detected" if damage_items else "No high-confidence road damage detected",
            "count": len(damage_items), "counts": damage_counts, "detections": damage_items,
            "last_scanned": now(),
        }
    except Exception as error:
        record["road_damage"] = {"status": f"Road scan error: {error}", "count": 0, "counts": {}, "detections": [], "last_scanned": now()}
    finally:
        record["road_scan_pending"] = False


def iou(left: list[float], right: list[float]) -> float:
    x1, y1 = max(left[0], right[0]), max(left[1], right[1])
    x2, y2 = min(left[2], right[2]), min(left[3], right[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = (left[2] - left[0]) * (left[3] - left[1]) + (right[2] - right[0]) * (right[3] - right[1]) - intersection
    return intersection / union if union else 0.0


TRACKED_VEHICLE_CLASSES = {"car", "bus", "truck", "motorcycle", "bicycle"}


def update_vehicle_tracks(record: dict[str, Any], detections: list[dict[str, Any]]) -> dict[str, Any]:
    """Maintain lightweight, per-bus vehicle IDs across sampled detector frames.

    Relative screen motion is used only as a risk indicator. It is deliberately not reported
    as km/h because a moving bus camera needs a calibrated road plane or vehicle sensors for that.
    """
    timestamp = time.monotonic()
    tracks: dict[str, dict[str, Any]] = record.setdefault("vehicle_tracks", {})
    next_id = record.setdefault("next_vehicle_track_id", 1)
    matched: set[str] = set()
    visible: list[dict[str, Any]] = []
    for detection in (item for item in detections if item["class"] in TRACKED_VEHICLE_CLASSES):
        candidates = [
            (iou(detection["box"], track["box"]), track_id, track)
            for track_id, track in tracks.items()
            if track["class"] == detection["class"] and track_id not in matched and timestamp - track["seen_at"] <= 2.5
        ]
        score, track_id, track = max(candidates, default=(0.0, "", None), key=lambda candidate: candidate[0])
        center = [(detection["box"][0] + detection["box"][2]) / 2, (detection["box"][1] + detection["box"][3]) / 2]
        if track is None or score < 0.18:
            track_id = str(next_id)
            next_id += 1
            track = {"track_id": track_id, "class": detection["class"], "box": detection["box"], "center": center,
                     "seen_at": timestamp, "observations": 1, "velocity": [0.0, 0.0], "history": [center]}
            tracks[track_id] = track
        else:
            elapsed = max(timestamp - track["seen_at"], 0.05)
            velocity = [(center[0] - track["center"][0]) / elapsed, (center[1] - track["center"][1]) / elapsed]
            track.update({"box": detection["box"], "center": center, "seen_at": timestamp,
                          "observations": track["observations"] + 1, "velocity": velocity,
                          "history": (track.get("history", []) + [center])[-8:]})
        matched.add(track_id)
        visible.append(track)
    record["next_vehicle_track_id"] = next_id
    for track_id in [key for key, value in tracks.items() if timestamp - value["seen_at"] > 5.0]:
        tracks.pop(track_id, None)
    vectors = [track["velocity"] for track in visible if track["observations"] >= 3]
    base_x = float(np.median([vector[0] for vector in vectors])) if vectors else 0.0
    base_y = float(np.median([vector[1] for vector in vectors])) if vectors else 0.0
    public_tracks = []
    risk_tracks = []
    for track in visible:
        relative_motion = float(np.hypot(track["velocity"][0] - base_x, track["velocity"][1] - base_y))
        risk = track["observations"] >= 3 and relative_motion >= 110
        item = {"track_id": track["track_id"], "class": track["class"], "box": track["box"],
                "observations": track["observations"], "relative_motion_px_s": round(relative_motion, 1),
                "risk_candidate": risk, "trajectory": track["history"]}
        public_tracks.append(item)
        if risk:
            risk_tracks.append(item)
    return {"active_tracks": len(public_tracks), "tracks": public_tracks, "risk_tracks": risk_tracks,
            "speed_unit": "relative screen motion (px/s)", "calibrated_speed": False}


def update_sidewalk_obstructions(
    record: dict[str, Any], tracking: dict[str, Any], side: str, width_fraction: float, frame_width: int,
) -> dict[str, Any]:
    """Flag a *stopped* vehicle only after it remains inside a configured sidewalk zone.

    A camera cannot reliably infer a sidewalk from arbitrary imagery alone. The driver or
    operator therefore configures a left/right image zone for the fixed camera position.
    This avoids calling an ordinary roadside vehicle an illegal-parking violation.
    """
    if side not in {"left", "right", "both"}:
        return {"status": "Sidewalk zone is off", "count": 0, "detections": [], "zone": "off"}
    width_fraction = min(max(width_fraction, 0.08), 0.45)
    timestamp = time.monotonic()
    candidates: dict[str, float] = record.setdefault("sidewalk_candidate_since", {})
    blocked: list[dict[str, Any]] = []
    visible_ids: set[str] = set()
    for track in tracking.get("tracks", []):
        if track["class"] not in TRACKED_VEHICLE_CLASSES or track["observations"] < 3:
            continue
        center_x = (track["box"][0] + track["box"][2]) / 2 / max(frame_width, 1)
        on_left = center_x <= width_fraction
        on_right = center_x >= 1 - width_fraction
        in_zone = (side in {"left", "both"} and on_left) or (side in {"right", "both"} and on_right)
        stopped = track["relative_motion_px_s"] <= 35
        if not (in_zone and stopped):
            candidates.pop(track["track_id"], None)
            continue
        visible_ids.add(track["track_id"])
        since = candidates.setdefault(track["track_id"], timestamp)
        duration = timestamp - since
        if duration >= 5:
            zone_side = "left" if on_left and not on_right else "right" if on_right and not on_left else side
            blocked.append({
                "track_id": track["track_id"], "class": track["class"], "confidence": 1.0,
                "box": track["box"], "stopped_seconds": round(duration, 1), "side": zone_side,
                "review_required": True,
            })
    for track_id in list(candidates):
        if track_id not in visible_ids:
            candidates.pop(track_id, None)
    status = "Potential sidewalk obstruction — officer review required" if blocked else "No stopped vehicle in configured sidewalk zone"
    return {"status": status, "count": len(blocked), "detections": blocked, "zone": f"{side} {width_fraction:.0%} frame edge"}


def persist_sidewalk_obstructions(record: dict[str, Any], items: list[dict[str, Any]]) -> None:
    """Store rate-limited, GPS-linked evidence; it is a review cue, not an enforcement decision."""
    if not items or record.get("latitude") is None or record.get("longitude") is None:
        return
    timestamp = time.time()
    if timestamp - record.get("last_sidewalk_obstruction_saved_at", 0.0) < 30:
        return
    highest = max(items, key=lambda item: item["stopped_seconds"])
    priority = min(100, round(55 + min(highest["stopped_seconds"], 30) * 1.5))
    with db_lock, database() as connection:
        connection.execute(
            """INSERT INTO sidewalk_obstruction_events
               (driver_id, latitude, longitude, vehicle_class, confidence, side, stopped_seconds, priority, detected_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record["driver_id"], record["latitude"], record["longitude"], highest["class"], highest["confidence"],
             highest["side"], highest["stopped_seconds"], priority, now()),
        )
    record["last_sidewalk_obstruction_saved_at"] = timestamp


def smooth_potholes(record: dict[str, Any], current: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Blend same-pothole boxes across consecutive frames to avoid visual jitter."""
    previous = record.get("pothole_tracks", [])
    for item in current:
        match = max((track for track in previous if iou(item["box"], track["box"]) >= 0.25), key=lambda track: iou(item["box"], track["box"]), default=None)
        if match:
            item["box"] = [round(0.72 * value + 0.28 * prior, 1) for value, prior in zip(item["box"], match["box"])]
    record["pothole_tracks"] = current
    return current


def defect_priority(item: dict[str, Any], frame_width: int, frame_height: int) -> int:
    """Rank likely urgent defects by confidence and the portion of the road image affected."""
    x1, y1, x2, y2 = item["box"]
    frame_area = max(frame_width * frame_height, 1)
    coverage = max(0.0, (x2 - x1) * (y2 - y1)) / frame_area
    return min(100, round(35 + item["confidence"] * 50 + min(coverage * 180, 15)))


def persist_potholes(record: dict[str, Any], items: list[dict[str, Any]], frame_width: int, frame_height: int) -> None:
    """Save one GPS-linked incident at a time instead of writing every live video frame."""
    if not items or record.get("latitude") is None or record.get("longitude") is None:
        return
    timestamp = time.time()
    if timestamp - record.get("last_defect_saved_at", 0.0) < 20:
        return
    highest = max(items, key=lambda item: item["confidence"])
    detected_at = now()
    with db_lock, database() as connection:
        connection.execute(
            """INSERT INTO infrastructure_defects
               (defect_type, driver_id, latitude, longitude, confidence, priority, status, detected_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'Detected', ?, ?)""",
            ("Pothole", record["driver_id"], record["latitude"], record["longitude"], highest["confidence"],
             defect_priority(highest, frame_width, frame_height), detected_at, detected_at),
        )
    record["last_defect_saved_at"] = timestamp


def persist_waterlogging(record: dict[str, Any], items: list[dict[str, Any]], frame_width: int, frame_height: int) -> None:
    """Save rate-limited, GPS-linked waterlogging evidence for the government work queue."""
    if not items or record.get("latitude") is None or record.get("longitude") is None:
        return
    timestamp = time.time()
    if timestamp - record.get("last_waterlogging_saved_at", 0.0) < 30:
        return
    highest = max(items, key=lambda item: item["confidence"])
    detected_at = now()
    with db_lock, database() as connection:
        connection.execute(
            """INSERT INTO infrastructure_defects
               (defect_type, driver_id, latitude, longitude, confidence, priority, status, detected_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'Detected', ?, ?)""",
            ("Waterlogging", record["driver_id"], record["latitude"], record["longitude"], highest["confidence"],
             defect_priority(highest, frame_width, frame_height), detected_at, detected_at),
        )
    record["last_waterlogging_saved_at"] = timestamp


def persist_speedbreakers(record: dict[str, Any], items: list[dict[str, Any]], frame_width: int, frame_height: int) -> None:
    """Save a GPS-linked speedbreaker observation at most once every 30 seconds per driver."""
    if not items or record.get("latitude") is None or record.get("longitude") is None:
        return
    timestamp = time.time()
    if timestamp - record.get("last_speedbreaker_saved_at", 0.0) < 30:
        return
    highest = max(items, key=lambda item: item["confidence"])
    detected_at = now()
    with db_lock, database() as connection:
        connection.execute(
            """INSERT INTO infrastructure_defects
               (defect_type, driver_id, latitude, longitude, confidence, priority, status, detected_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'Detected', ?, ?)""",
            ("Speedbreaker", record["driver_id"], record["latitude"], record["longitude"], highest["confidence"],
             defect_priority(highest, frame_width, frame_height), detected_at, detected_at),
        )
    record["last_speedbreaker_saved_at"] = timestamp


def persist_zebra_crossings(record: dict[str, Any], items: list[dict[str, Any]], frame_width: int, frame_height: int) -> None:
    """Record existing crossing locations for the GIS inventory; never label them as defects."""
    if not items or record.get("latitude") is None or record.get("longitude") is None:
        return
    timestamp = time.time()
    if timestamp - record.get("last_zebra_crossing_saved_at", 0.0) < 60:
        return
    highest = max(items, key=lambda item: item["confidence"])
    detected_at = now()
    with db_lock, database() as connection:
        connection.execute(
            """INSERT INTO infrastructure_defects
               (defect_type, driver_id, latitude, longitude, confidence, priority, status, detected_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'Detected', ?, ?)""",
            ("Zebra crossing (inventory)", record["driver_id"], record["latitude"], record["longitude"], highest["confidence"],
             defect_priority(highest, frame_width, frame_height), detected_at, detected_at),
        )
    record["last_zebra_crossing_saved_at"] = timestamp


def persist_road_dividers(record: dict[str, Any], items: list[dict[str, Any]], frame_width: int, frame_height: int) -> None:
    """Record observed dividers as GIS inventory records; present dividers are not infrastructure defects."""
    if not items or record.get("latitude") is None or record.get("longitude") is None:
        return
    timestamp = time.time()
    if timestamp - record.get("last_road_divider_saved_at", 0.0) < 60:
        return
    highest = max(items, key=lambda item: item["confidence"])
    detected_at = now()
    with db_lock, database() as connection:
        connection.execute(
            """INSERT INTO infrastructure_defects
               (defect_type, driver_id, latitude, longitude, confidence, priority, status, detected_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, 'Detected', ?, ?)""",
            ("Road divider (inventory)", record["driver_id"], record["latitude"], record["longitude"], highest["confidence"],
             defect_priority(highest, frame_width, frame_height), detected_at, detected_at),
        )
    record["last_road_divider_saved_at"] = timestamp


def persist_traffic_event(record: dict[str, Any], counts: dict[str, int]) -> None:
    """Capture one actionable, GPS-linked vehicle-density observation every 20 seconds."""
    if record.get("latitude") is None or record.get("longitude") is None:
        return
    cars, bikes, buses = counts.get("car", 0), counts.get("motorcycle", 0) + counts.get("bicycle", 0), counts.get("bus", 0)
    total = cars + bikes + buses + counts.get("truck", 0)
    if total == 0 or time.time() - record.get("last_traffic_saved_at", 0.0) < 20:
        return
    density = "High" if total >= 6 else "Moderate" if total >= 3 else "Low"
    estimated_delay = 8 if density == "High" else 4 if density == "Moderate" else 1
    insight = (
        "Deploy traffic management or review signal timing; this camera scene indicates a likely local delay."
        if density == "High" else
        "Monitor this route segment; vehicle density may build into a delay." if density == "Moderate" else
        "Traffic flow appears light in this camera scene."
    )
    priority = min(100, 25 + total * 10 + buses * 8)
    captured_at = now()
    with db_lock, database() as connection:
        connection.execute(
            """INSERT INTO traffic_analysis_events
               (driver_id, latitude, longitude, cars, bikes, buses, total_vehicles, density, estimated_delay_minutes, insight, priority, status, detected_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Detected', ?, ?)""",
            (record["driver_id"], record["latitude"], record["longitude"], cars, bikes, buses, total, density,
             estimated_delay, insight, priority, captured_at, captured_at),
        )
    record["last_traffic_saved_at"] = time.time()


def congestion_level(total_vehicles: float) -> str:
    if total_vehicles >= 6:
        return "High"
    if total_vehicles >= 3:
        return "Moderate"
    return "Low"


def build_congestion_forecast(driver_id: str, history: list[dict[str, Any]], route: dict[str, Any] | None) -> dict[str, Any]:
    """Use recent camera-count trend as a bounded short-horizon congestion estimate.

    This deliberately avoids claiming road speed or ETA: those require map-matched route and
    speed feeds that are not available from a single camera.
    """
    recent = history[-6:]
    latest = recent[-1]
    counts = [item["total_vehicles"] for item in recent]
    baseline = sum(counts) / len(counts)
    trend_per_minute = 0.0
    elapsed_minutes = 0.0
    if len(recent) >= 2:
        try:
            first_time = datetime.fromisoformat(recent[0]["detected_at"])
            last_time = datetime.fromisoformat(recent[-1]["detected_at"])
            elapsed_minutes = max((last_time - first_time).total_seconds() / 60, 0.0)
            if elapsed_minutes >= 0.5:
                trend_per_minute = (counts[-1] - counts[0]) / elapsed_minutes
        except (TypeError, ValueError):
            elapsed_minutes = 0.0
    # Camera scenes vary quickly. Bound the trend so a short burst cannot become an extreme forecast.
    trend_per_minute = max(-0.5, min(0.5, trend_per_minute))
    confidence = "Medium" if len(recent) >= 4 and elapsed_minutes >= 1.0 else "Low"
    projections = []
    for minutes in (5, 10, 15):
        estimate = max(0, min(20, round(baseline + trend_per_minute * minutes)))
        level = congestion_level(estimate)
        projections.append({
            "minutes": minutes,
            "estimated_vehicles": estimate,
            "density": level,
            "estimated_delay_minutes": 8 if level == "High" else 4 if level == "Moderate" else 1,
        })
    return {
        "driver_id": driver_id,
        "source": route["source"] if route else "Route not configured",
        "destination": route["destination"] if route else "Route not configured",
        "location": {"latitude": latest["latitude"], "longitude": latest["longitude"]},
        "samples": len(recent),
        "confidence": confidence,
        "trend": "Increasing" if trend_per_minute >= 0.15 else "Decreasing" if trend_per_minute <= -0.15 else "Stable",
        "projections": projections,
    }


def process_pothole_video(job_id: str, source: Path, target: Path, confidence: float) -> None:
    """Background OpenCV pipeline based on PyResearch's YOLO + Supervision architecture."""
    import torch

    job = video_jobs[job_id]
    cap = cv2.VideoCapture(str(source))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if width < 2 or height < 2:
        job.update({"status": "failed", "error": "The uploaded file is not a readable video."})
        cap.release()
        return
    writer = cv2.VideoWriter(str(target), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        job.update({"status": "failed", "error": "Could not create the processed MP4."})
        cap.release()
        return
    runtime = device_details()
    model = get_pothole_model()
    frame_number = 0
    last_items: list[dict[str, Any]] = []
    inference_ms = 0.0
    skip = max(1, int(round(fps / 8)))  # target approximately 8 pothole inferences/sec
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_number += 1
            if frame_number == 1 or frame_number % skip == 0:
                started = time.perf_counter()
                with model_lock, torch.inference_mode():
                    result = model(frame, conf=confidence, verbose=False, device=0 if runtime["fp16"] else "cpu", half=runtime["fp16"])[0]
                inference_ms = (time.perf_counter() - started) * 1000
                last_items = []
                for class_id, score, box in zip(result.boxes.cls, result.boxes.conf, result.boxes.xyxy):
                    if "pothole" not in result.names[int(class_id)].lower():
                        continue
                    last_items.append({"class": "Pothole", "confidence": float(score), "box": [float(value) for value in box]})
            annotated = frame.copy()
            for item in last_items:
                x1, y1, x2, y2 = map(int, item["box"])
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (30, 30, 225), 2)
                text = f"Pothole {item['confidence']:.0%}"
                cv2.putText(annotated, text, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 225), 2)
            writer.write(annotated)
            elapsed = max(time.perf_counter() - job["started_at"], 0.001)
            job.update({"processed_frames": frame_number, "total_frames": total_frames, "pothole_count": len(last_items),
                        "confidence": round(max((item["confidence"] for item in last_items), default=0.0), 4),
                        "fps": round(frame_number / elapsed, 1), "latency_ms": round(inference_ms, 1),
                        "device": runtime["device"], "frame_skip": skip})
        job.update({"status": "complete", "download_url": f"/api/pothole-video/{job_id}/download"})
    except Exception as error:
        job.update({"status": "failed", "error": str(error)})
    finally:
        cap.release()
        writer.release()


@app.get("/", include_in_schema=False)
def index() -> RedirectResponse:
    return RedirectResponse("/driver")


@app.get("/driver", include_in_schema=False)
def driver_dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "driver.html")


@app.get("/government", include_in_schema=False)
def government_dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "government.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ready",
        "model": MODEL_PATH.name,
        "pothole_model": POTHOLE_VIDEO_MODEL_PATH.name,
        "pothole_model_available": str(POTHOLE_VIDEO_MODEL_PATH.exists()),
        "waterlogging_model": WATERLOGGING_MODEL_PATH.name,
        "waterlogging_model_available": str(WATERLOGGING_MODEL_PATH.exists()),
        "speedbreaker_model": str(SPEEDBREAKER_MODEL_PATH.relative_to(ROOT)),
        "speedbreaker_model_available": str(SPEEDBREAKER_MODEL_PATH.exists()),
        "zebra_crossing_model": str(ZEBRA_CROSSING_MODEL_PATH.relative_to(ROOT)),
        "zebra_crossing_model_available": str(ZEBRA_CROSSING_MODEL_PATH.exists()),
        "road_divider_model": str(ROAD_DIVIDER_MODEL_PATH.relative_to(ROOT)),
        "road_divider_model_available": str(ROAD_DIVIDER_MODEL_PATH.exists()),
        "license_plate_model": str(PLATE_MODEL_PATH.relative_to(ROOT)),
        "license_plate_model_available": str(PLATE_MODEL_PATH.exists()),
        "pyresearch_checkpoint": "installed but incompatible with the current Ultralytics runtime; compatible fallback enabled",
        "annotator": "supervision",
    }


@app.post("/api/pothole-video")
async def submit_pothole_video(video: UploadFile = File(...), confidence: float = Form(0.35)) -> dict[str, Any]:
    if not 0.05 <= confidence <= 0.95:
        raise HTTPException(status_code=422, detail="Confidence must be between 0.05 and 0.95")
    if not (video.content_type or "").startswith("video/"):
        raise HTTPException(status_code=415, detail="Upload a video file (MP4, MOV, AVI, or WebM).")
    get_pothole_model()  # fail early and clearly if the compatible model is not installed
    job_id = uuid.uuid4().hex
    source = VIDEO_DIR / f"{job_id}_source.mp4"
    target = VIDEO_DIR / f"{job_id}_potholes.mp4"
    with source.open("wb") as output:
        shutil.copyfileobj(video.file, output)
    job = {"id": job_id, "status": "processing", "started_at": time.perf_counter(), "processed_frames": 0,
           "total_frames": 0, "pothole_count": 0, "confidence": 0.0, "fps": 0.0, "latency_ms": 0.0,
           **device_details()}
    video_jobs[job_id] = job
    threading.Thread(target=process_pothole_video, args=(job_id, source, target, confidence), daemon=True).start()
    return {"job_id": job_id, "status_url": f"/api/pothole-video/{job_id}"}


def infer_pothole_frame(frame: np.ndarray, driver_id: str, confidence: float) -> dict[str, Any]:
    """CPU/GPU work happens in a worker thread so the API event loop stays responsive."""
    started = time.perf_counter()
    import torch

    with road_model_lock, torch.inference_mode():
        result = get_road_damage_model()(frame, conf=max(confidence, ROAD_DAMAGE_CONFIDENCE), imgsz=512, verbose=False)[0]
    items = []
    counts: dict[str, int] = {}
    for class_id, score, box in zip(result.boxes.cls, result.boxes.conf, result.boxes.xyxy):
        label = result.names[int(class_id)]
        if "pothole" not in label.lower():
            continue
        counts["Pothole"] = counts.get("Pothole", 0) + 1
        items.append({"class": "Pothole", "confidence": round(float(score), 4), "box": [round(float(value), 1) for value in box]})
    record = state(driver_id)
    items = smooth_potholes(record, items)
    latency = (time.perf_counter() - started) * 1000
    record["road_damage"] = {"status": "Damage detected" if items else "No high-confidence road damage detected", "count": len(items),
                             "counts": counts, "detections": items, "last_scanned": now()}
    persist_potholes(record, items, frame.shape[1], frame.shape[0])
    return {"detections": items, "count": len(items), "counts": counts, "confidence": round(max((item["confidence"] for item in items), default=0.0), 4),
            "latency_ms": round(latency, 1), "fps": round(1000 / latency, 1) if latency else 0, "frame_width": frame.shape[1], "frame_height": frame.shape[0]}


@app.post("/api/pothole-frame")
async def pothole_frame(
    image: UploadFile = File(...),
    driver_id: str = Form(...),
    confidence: float = Form(ROAD_DAMAGE_CONFIDENCE),
) -> dict[str, Any]:
    """Dedicated low-latency pothole channel; it does not wait for object detection."""
    content = await image.read()
    frame = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=415, detail="Could not read the video frame")
    return await run_in_threadpool(infer_pothole_frame, frame, driver_id, confidence)


def infer_waterlogging_frame(frame: np.ndarray, driver_id: str, confidence: float) -> dict[str, Any]:
    """Dedicated, rate-limited waterlogging detector. It never changes object or pothole results."""
    started = time.perf_counter()
    import torch

    with waterlogging_model_lock, torch.inference_mode():
        detector = get_waterlogging_model()
        # The legacy model labels waterlogging as class 2; the new one-class
        # road-water model labels it as class 0. Resolve by class name so the
        # independent stream works correctly with either checkpoint.
        names = detector.names
        name_items = names.items() if isinstance(names, dict) else enumerate(names)
        class_ids = [index for index, label in name_items if "water" in str(label).lower()]
        is_candidate = WATERLOGGING_MODEL_PATH == WATERLOGGING_CANDIDATE_MODEL_PATH
        result = detector(
            frame,
            conf=max(confidence, 0.35 if is_candidate else 0.55),
            imgsz=640 if is_candidate else 512,
            classes=class_ids or None,
            verbose=False,
        )[0]
    items = []
    if result.boxes is not None:
        items = [
            {"class": "Waterlogging", "confidence": round(float(score), 4), "box": [round(float(value), 1) for value in box]}
            for score, box in zip(result.boxes.conf, result.boxes.xyxy)
        ]
    record = state(driver_id)
    latency = (time.perf_counter() - started) * 1000
    record["waterlogging"] = {"status": "Waterlogging detected" if items else "No high-confidence waterlogging detected", "count": len(items), "detections": items, "last_scanned": now()}
    persist_waterlogging(record, items, frame.shape[1], frame.shape[0])
    return {"detections": items, "count": len(items), "confidence": round(max((item["confidence"] for item in items), default=0.0), 4),
            "latency_ms": round(latency, 1), "fps": round(1000 / latency, 1) if latency else 0,
            "frame_width": frame.shape[1], "frame_height": frame.shape[0]}


@app.post("/api/waterlogging-frame")
async def waterlogging_frame(
    image: UploadFile = File(...),
    driver_id: str = Form(...),
    confidence: float = Form(0.55),
) -> dict[str, Any]:
    """Independent waterlogging channel; called less frequently so video remains responsive."""
    content = await image.read()
    frame = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=415, detail="Could not read the video frame")
    return await run_in_threadpool(infer_waterlogging_frame, frame, driver_id, confidence)


def infer_speedbreaker_frame(frame: np.ndarray, driver_id: str, confidence: float) -> dict[str, Any]:
    """Independent speedbreaker detector; never shares results with pothole or object scans."""
    started = time.perf_counter()
    import torch

    with speedbreaker_model_lock, torch.inference_mode():
        result = get_speedbreaker_model()(frame, conf=max(confidence, 0.50), imgsz=512, verbose=False)[0]
    items = []
    if result.boxes is not None:
        items = [
            {"class": "Speedbreaker", "confidence": round(float(score), 4), "box": [round(float(value), 1) for value in box]}
            for score, box in zip(result.boxes.conf, result.boxes.xyxy)
        ]
    record = state(driver_id)
    latency = (time.perf_counter() - started) * 1000
    record["speedbreakers"] = {"status": "Speedbreaker detected" if items else "No high-confidence speedbreaker detected", "count": len(items), "detections": items, "last_scanned": now()}
    persist_speedbreakers(record, items, frame.shape[1], frame.shape[0])
    return {"detections": items, "count": len(items), "confidence": round(max((item["confidence"] for item in items), default=0.0), 4),
            "latency_ms": round(latency, 1), "fps": round(1000 / latency, 1) if latency else 0,
            "frame_width": frame.shape[1], "frame_height": frame.shape[0]}


@app.post("/api/speedbreaker-frame")
async def speedbreaker_frame(
    image: UploadFile = File(...),
    driver_id: str = Form(...),
    confidence: float = Form(0.50),
) -> dict[str, Any]:
    content = await image.read()
    frame = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=415, detail="Could not read the video frame")
    return await run_in_threadpool(infer_speedbreaker_frame, frame, driver_id, confidence)


def infer_zebra_crossing_frame(frame: np.ndarray, driver_id: str, confidence: float) -> dict[str, Any]:
    """Independent zebra-crossing inventory scan. Existing crossings are not classified as missing/defective."""
    started = time.perf_counter()
    import torch

    with zebra_crossing_model_lock, torch.inference_mode():
        result = get_zebra_crossing_model()(frame, conf=max(confidence, 0.50), imgsz=512, verbose=False)[0]
    items = []
    if result.boxes is not None:
        items = [
            {"class": "Zebra crossing", "confidence": round(float(score), 4), "box": [round(float(value), 1) for value in box]}
            for score, box in zip(result.boxes.conf, result.boxes.xyxy)
        ]
    record = state(driver_id)
    latency = (time.perf_counter() - started) * 1000
    record["zebra_crossings"] = {"status": "Zebra crossing detected" if items else "No high-confidence zebra crossing detected", "count": len(items), "detections": items, "last_scanned": now()}
    persist_zebra_crossings(record, items, frame.shape[1], frame.shape[0])
    return {"detections": items, "count": len(items), "confidence": round(max((item["confidence"] for item in items), default=0.0), 4),
            "latency_ms": round(latency, 1), "fps": round(1000 / latency, 1) if latency else 0,
            "frame_width": frame.shape[1], "frame_height": frame.shape[0]}


@app.post("/api/zebra-crossing-frame")
async def zebra_crossing_frame(
    image: UploadFile = File(...),
    driver_id: str = Form(...),
    confidence: float = Form(0.50),
) -> dict[str, Any]:
    content = await image.read()
    frame = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=415, detail="Could not read the video frame")
    return await run_in_threadpool(infer_zebra_crossing_frame, frame, driver_id, confidence)


def infer_road_divider_frame(frame: np.ndarray, driver_id: str, confidence: float) -> dict[str, Any]:
    """Independent divider-present inventory scan; absence cannot be inferred from this checkpoint."""
    started = time.perf_counter()
    import torch

    with road_divider_model_lock, torch.inference_mode():
        result = get_road_divider_model()(frame, conf=max(confidence, 0.50), imgsz=512, verbose=False)[0]
    items = []
    if result.boxes is not None:
        items = [
            {"class": "Road divider", "confidence": round(float(score), 4), "box": [round(float(value), 1) for value in box]}
            for score, box in zip(result.boxes.conf, result.boxes.xyxy)
        ]
    record = state(driver_id)
    latency = (time.perf_counter() - started) * 1000
    record["road_dividers"] = {"status": "Road divider detected" if items else "No high-confidence road divider detected", "count": len(items), "detections": items, "last_scanned": now()}
    persist_road_dividers(record, items, frame.shape[1], frame.shape[0])
    return {"detections": items, "count": len(items), "confidence": round(max((item["confidence"] for item in items), default=0.0), 4),
            "latency_ms": round(latency, 1), "fps": round(1000 / latency, 1) if latency else 0,
            "frame_width": frame.shape[1], "frame_height": frame.shape[0]}


@app.post("/api/road-divider-frame")
async def road_divider_frame(
    image: UploadFile = File(...),
    driver_id: str = Form(...),
    confidence: float = Form(0.50),
) -> dict[str, Any]:
    content = await image.read()
    frame = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=415, detail="Could not read the video frame")
    return await run_in_threadpool(infer_road_divider_frame, frame, driver_id, confidence)


def accident_severity(confidence: float) -> str:
    return "High" if confidence >= 0.75 else "Medium" if confidence >= 0.55 else "Low"


def infer_accident_frame(frame: np.ndarray, driver_id: str) -> dict[str, Any]:
    """Independent accident and plate-localization channel; OCR is intentionally not guessed."""
    started = time.perf_counter()
    import torch

    with accident_model_lock, torch.inference_mode():
        accident_result = get_accident_model()(frame, conf=0.45, imgsz=640, verbose=False)[0]
        # First pass catches large plates. The lower threshold is filtered again by a vehicle ROI pass below.
        plate_result = get_plate_model()(frame, conf=0.12, imgsz=960, verbose=False)[0]
        with model_lock:
            vehicle_result = get_model()(frame, conf=0.28, imgsz=640, verbose=False)[0]
    accidents = [{"class": "Accident", "confidence": round(float(score), 4),
                  "box": [round(float(value), 1) for value in box]}
                 for score, box in zip(accident_result.boxes.conf, accident_result.boxes.xyxy)]
    plates = [{"class": "License plate", "confidence": round(float(score), 4),
               "box": [round(float(value), 1) for value in box], "text": "OCR candidate unavailable"}
              for score, box in zip(plate_result.boxes.conf, plate_result.boxes.xyxy)]
    vehicle_labels = {"car", "motorcycle", "bus", "truck"}
    # A plate is tiny compared with a 640px road frame. Re-running inside each vehicle crop gives it far
    # more pixels, which is particularly important for motorcycle plates and tilted Indian plates.
    for class_id, vehicle_box in zip(vehicle_result.boxes.cls, vehicle_result.boxes.xyxy):
        if vehicle_result.names[int(class_id)] not in vehicle_labels:
            continue
        vx1, vy1, vx2, vy2 = (int(value) for value in vehicle_box)
        pad_x, pad_y = int((vx2 - vx1) * 0.08), int((vy2 - vy1) * 0.08)
        x1, y1 = max(0, vx1 - pad_x), max(0, vy1 - pad_y)
        x2, y2 = min(frame.shape[1], vx2 + pad_x), min(frame.shape[0], vy2 + pad_y)
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            continue
        roi_result = get_plate_model()(roi, conf=0.08, imgsz=960, verbose=False)[0]
        for score, plate_box in zip(roi_result.boxes.conf, roi_result.boxes.xyxy):
            px1, py1, px2, py2 = (float(value) for value in plate_box)
            candidate = {"class": "License plate", "confidence": round(float(score), 4),
                         "box": [round(x1 + px1, 1), round(y1 + py1, 1), round(x1 + px2, 1), round(y1 + py2, 1)],
                         "text": "OCR candidate unavailable"}
            if not any(iou(candidate["box"], item["box"]) >= 0.35 for item in plates):
                plates.append(candidate)
    confidence = max((item["confidence"] for item in accidents), default=0.0)
    severity = accident_severity(confidence) if accidents else None
    record = state(driver_id)
    incident_id = None
    if accidents and record.get("latitude") is not None and record.get("longitude") is not None:
        timestamp = time.time()
        if timestamp - record.get("last_accident_saved_at", 0.0) >= 30:
            evidence_token = uuid.uuid4().hex
            evidence_name = f"accident_{evidence_token}.jpg"
            evidence_path = ACCIDENT_EVIDENCE_DIR / evidence_name
            cv2.imwrite(str(evidence_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            for index, plate in enumerate(plates, start=1):
                x1, y1, x2, y2 = (int(value) for value in plate["box"])
                crop = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]
                if crop.size:
                    crop_name = f"plate_{evidence_token}_{index}.jpg"
                    cv2.imwrite(str(ACCIDENT_EVIDENCE_DIR / crop_name), crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    plate["crop_url"] = f"/api/accidents/evidence/{crop_name}"
            captured_at = now()
            with db_lock, database() as connection:
                cursor = connection.execute(
                    """INSERT INTO accident_incidents
                       (driver_id, latitude, longitude, confidence, severity, plates_json, evidence_path, detected_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (driver_id, record["latitude"], record["longitude"], confidence, severity,
                     json.dumps(plates), f"/api/accidents/evidence/{evidence_name}", captured_at),
                )
                incident_id = cursor.lastrowid
            record["last_accident_saved_at"] = timestamp
    latency = (time.perf_counter() - started) * 1000
    return {"accidents": accidents, "plates": plates, "severity": severity, "incident_id": incident_id,
            "confidence": confidence, "latency_ms": round(latency, 1), "frame_width": frame.shape[1], "frame_height": frame.shape[0]}


@app.post("/api/accident-frame")
async def accident_frame(image: UploadFile = File(...), driver_id: str = Form(...)) -> dict[str, Any]:
    content = await image.read()
    frame = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=415, detail="Could not read the accident analysis frame")
    return await run_in_threadpool(infer_accident_frame, frame, driver_id)


@app.get("/api/pothole-video/{job_id}")
def pothole_video_status(job_id: str) -> dict[str, Any]:
    if job_id not in video_jobs:
        raise HTTPException(status_code=404, detail="Video job not found")
    job = video_jobs[job_id].copy()
    job.pop("started_at", None)
    return job


@app.get("/api/pothole-video/{job_id}/download")
def download_pothole_video(job_id: str) -> FileResponse:
    target = VIDEO_DIR / f"{job_id}_potholes.mp4"
    if job_id not in video_jobs or video_jobs[job_id]["status"] != "complete" or not target.exists():
        raise HTTPException(status_code=404, detail="Processed video is not ready")
    return FileResponse(target, media_type="video/mp4", filename="pothole_detection.mp4")


@app.post("/api/location")
def update_location(location: LocationUpdate) -> dict[str, Any]:
    ensure_bus_record(location.driver_id)
    record = state(location.driver_id)
    record.update(location.model_dump())
    record["last_seen"] = now()
    return {"ok": True, "last_seen": record["last_seen"]}


@app.post("/api/detect")
async def detect(
    image: UploadFile = File(...),
    driver_id: str = Form(...),
    confidence: float = Form(0.35),
    sidewalk_side: str = Form("off"),
    sidewalk_width: float = Form(0.22),
) -> dict[str, Any]:
    if not 0.05 <= confidence <= 0.95:
        raise HTTPException(status_code=422, detail="Confidence must be between 0.05 and 0.95")
    ensure_bus_record(driver_id)
    content = await image.read()
    frame = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=415, detail="Upload a readable image or video frame")

    # Primary detector is deliberately isolated from the slower road model.
    with model_lock:
        result = get_model()(frame, conf=confidence, verbose=False)[0]
    detections = sv.Detections.from_ultralytics(result)
    names = result.names
    labels = [f"{names[int(class_id)]} {score:.0%}" for class_id, score in zip(detections.class_id, detections.confidence)]
    annotated = box_annotator.annotate(scene=frame.copy(), detections=detections)
    annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
    items = []
    for class_id, score, box in zip(detections.class_id, detections.confidence, detections.xyxy):
        items.append({"class": names[int(class_id)], "confidence": round(float(score), 4),
                      "box": [round(float(value), 1) for value in box]})
    counts: dict[str, int] = {}
    for item in items:
        counts[item["class"]] = counts.get(item["class"], 0) + 1
    person_count = counts.get("person", 0)
    vehicle_classes = {"car", "bus", "truck", "motorcycle", "bicycle"}
    vehicle_count = sum(counts.get(label, 0) for label in vehicle_classes)
    density = "High" if person_count >= 5 or vehicle_count >= 6 else "Moderate" if person_count >= 2 or vehicle_count >= 3 else "Low"
    record = state(driver_id)
    tracking = update_vehicle_tracks(record, items)
    sidewalk = update_sidewalk_obstructions(record, tracking, sidewalk_side, sidewalk_width, frame.shape[1])
    record["sidewalk_obstructions"] = {**sidewalk, "last_scanned": now()}
    persist_sidewalk_obstructions(record, sidewalk["detections"])
    alerts = []
    if person_count and vehicle_count:
        alerts.append({"level": "caution", "message": "Pedestrian near moving-traffic scene. Driver should slow down and scan the road."})
    if person_count >= 3:
        alerts.append({"level": "warning", "message": "High pedestrian density detected. Treat this as a crossing-risk warning."})
    if vehicle_count >= 5:
        alerts.append({"level": "warning", "message": "High vehicle density detected. Government dashboard flags possible local delay."})
    for track in tracking["risk_tracks"]:
        alerts.append({"level": "warning", "message": f"Possible rapid relative movement: {track['class']} Track #{track['track_id']}. Review video before treating this as rash driving."})
    if sidewalk["count"]:
        alerts.append({"level": "warning", "message": f"Potential sidewalk obstruction: {sidewalk['count']} stopped vehicle(s) in the configured sidewalk zone. Officer review required."})
    analysis = {"density": density, "vehicle_count": vehicle_count, "person_count": person_count,
                "counts": counts, "alerts": alerts, "tracking": tracking, "sidewalk_obstructions": sidewalk,
                "limitations": "Sidewalk-obstruction results require a correctly configured fixed-camera zone and officer review; they do not prove an illegal-parking offence."}
    image_data = encode_jpeg(annotated)
    # The dedicated /api/pothole-frame channel drives continuous road-damage updates.
    record.update({"last_seen": now(), "detections": items, "last_frame": image_data, "analysis": analysis, "scans": record["scans"] + 1})
    persist_traffic_event(record, counts)
    return {"driver_id": driver_id, "timestamp": record["last_seen"], "count": len(items), "detections": items, "analysis": analysis, "tracking": tracking, "sidewalk_obstructions": sidewalk, "image": image_data,
            "road_damage": record["road_damage"], "frame_width": int(frame.shape[1]), "frame_height": int(frame.shape[0])}


@app.get("/api/vehicles")
def vehicles() -> list[dict[str, Any]]:
    return list(drivers.values())


def bus_is_online(record: dict[str, Any] | None) -> bool:
    if not record or not record.get("last_seen"):
        return False
    try:
        seen = datetime.fromisoformat(record["last_seen"])
        return (datetime.now(UTC) - seen.astimezone(UTC)).total_seconds() <= 20
    except (TypeError, ValueError):
        return False


@app.post("/api/buses", status_code=201)
def add_bus(bus: BusCreate) -> dict[str, Any]:
    bus_number = bus.bus_number.strip()
    source, destination = bus.source.strip(), bus.destination.strip()
    if (bus.latitude is None) != (bus.longitude is None):
        raise HTTPException(status_code=422, detail="Enter both latitude and longitude, or leave both blank.")
    if not bus_number or not source or not destination:
        raise HTTPException(status_code=422, detail="Bus number, source, and destination are required.")
    with db_lock, database() as connection:
        try:
            connection.execute(
                """INSERT INTO buses (bus_number, source, destination, latitude, longitude, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (bus_number, source, destination, bus.latitude, bus.longitude, now(), now()),
            )
        except sqlite3.IntegrityError as error:
            raise HTTPException(status_code=409, detail=f"Bus {bus_number} already exists. Use a different bus number.") from error
        row = connection.execute("SELECT * FROM buses WHERE bus_number = ?", (bus_number,)).fetchone()
    return dict(row)


@app.get("/api/buses")
def buses() -> list[dict[str, Any]]:
    """Official bus registry enriched with the latest in-memory driver-camera state."""
    with db_lock, database() as connection:
        registered = [dict(row) for row in connection.execute("SELECT * FROM buses ORDER BY bus_number COLLATE NOCASE")]
        accidents_by_bus = {
            row["driver_id"]: dict(row)
            for row in connection.execute(
                """SELECT a.* FROM accident_incidents a
                   INNER JOIN (SELECT driver_id, MAX(id) AS latest_id FROM accident_incidents GROUP BY driver_id) latest
                   ON a.id = latest.latest_id"""
            )
        }
    result: list[dict[str, Any]] = []
    for bus in registered:
        record = drivers.get(bus["bus_number"])
        online = bus_is_online(record)
        analysis = (record or {}).get("analysis", {})
        incident = accidents_by_bus.get(bus["bus_number"])
        result.append({
            **bus,
            "online": online,
            "last_seen": (record or {}).get("last_seen"),
            "live_latitude": (record or {}).get("latitude"),
            "live_longitude": (record or {}).get("longitude"),
            "object_count": len((record or {}).get("detections", [])) if online else 0,
            "vehicle_count": analysis.get("vehicle_count", 0) if online else 0,
            "density": analysis.get("density", "Unknown") if online else "Offline",
            "accident_status": (f"{incident['severity']} detected" if incident else "Not detected") if online else "Offline",
            "latest_accident_id": incident["id"] if incident else None,
        })
    return sorted(result, key=lambda item: (not item["online"], item["bus_number"].lower()))


@app.get("/api/analytics")
def analytics() -> dict[str, Any]:
    active = list(drivers.values())
    total_vehicles = sum(record["analysis"]["vehicle_count"] for record in active)
    total_people = sum(record["analysis"]["person_count"] for record in active)
    total_damage = sum(record["road_damage"]["count"] for record in active)
    delayed = [record["driver_id"] for record in active if record["analysis"]["vehicle_count"] >= 5]
    return {"active_drivers": len(active), "vehicle_observations": total_vehicles,
            "pedestrian_observations": total_people, "road_damage_observations": total_damage, "possible_delay_routes": delayed,
            "note": "Delay status is a camera-scene density heuristic, not a verified traffic-speed measurement."}


@app.get("/api/infrastructure-defects")
def infrastructure_defects() -> dict[str, Any]:
    """Government work queue backed by a local SQLite database."""
    with db_lock, database() as connection:
        defects = [dict(row) for row in connection.execute(
            "SELECT * FROM infrastructure_defects ORDER BY detected_at DESC LIMIT 200"
        )]
        priority_queue = [dict(row) for row in connection.execute(
            """SELECT * FROM infrastructure_defects
               WHERE status != 'Solved' ORDER BY priority DESC, detected_at DESC LIMIT 10"""
        )]
    counts = {"Detected": 0, "In progress": 0, "Solved": 0}
    for defect in defects:
        counts[defect["status"]] = counts.get(defect["status"], 0) + 1
    return {"defects": defects, "counts": counts, "priority_queue": priority_queue}


@app.get("/api/sidewalk-obstructions")
def sidewalk_obstructions() -> dict[str, Any]:
    """Officer-review queue for vehicles stopped in configured pedestrian sidewalk zones."""
    with db_lock, database() as connection:
        events = [dict(row) for row in connection.execute(
            "SELECT * FROM sidewalk_obstruction_events ORDER BY detected_at DESC LIMIT 200"
        )]
        priority_queue = [dict(row) for row in connection.execute(
            "SELECT * FROM sidewalk_obstruction_events ORDER BY priority DESC, detected_at DESC LIMIT 10"
        )]
    return {"events": events, "priority_queue": priority_queue}


@app.get("/api/accidents")
def accidents() -> dict[str, Any]:
    with db_lock, database() as connection:
        incidents = [dict(row) for row in connection.execute("SELECT * FROM accident_incidents ORDER BY detected_at DESC LIMIT 100")]
    for incident in incidents:
        incident["plates"] = json.loads(incident.pop("plates_json"))
    return {"incidents": incidents, "high_count": sum(item["severity"] == "High" for item in incidents)}


@app.get("/api/accidents/evidence/{filename}")
def accident_evidence(filename: str) -> FileResponse:
    target = ACCIDENT_EVIDENCE_DIR / Path(filename).name
    if not target.exists():
        raise HTTPException(status_code=404, detail="Accident evidence not found")
    return FileResponse(target, media_type="image/jpeg")


@app.get("/api/accidents/{incident_id}/report.pdf")
def accident_report(incident_id: int) -> FileResponse:
    """Create an official, evidence-backed incident briefing for traffic-authority review."""
    with db_lock, database() as connection:
        incident = connection.execute("SELECT * FROM accident_incidents WHERE id = ?", (incident_id,)).fetchone()
    if incident is None:
        raise HTTPException(status_code=404, detail="Accident incident not found")
    item = dict(incident)
    plates = json.loads(item["plates_json"])
    detected = datetime.fromisoformat(item["detected_at"])
    # A unique file prevents a second click from overwriting a PDF while the first one is downloading.
    report_path = PDF_DIR / f"accident_incident_{incident_id}_{uuid.uuid4().hex}_report.pdf"
    document = SimpleDocTemplate(str(report_path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm)
    styles = getSampleStyleSheet()
    story: list[Any] = [
        Paragraph("ROADWATCH GIS", styles["Title"]),
        Paragraph("Official Road Traffic Incident Report", styles["Heading2"]),
        Paragraph("Prepared for Government Traffic Authority - AI-assisted evidence; officer verification required.", styles["BodyText"]),
        Spacer(1, 7 * mm),
    ]
    plate_summary = "; ".join(f"plate crop {index}: {plate.get('confidence', 0):.0%} detection confidence" for index, plate in enumerate(plates, start=1)) or "No plate crop was detected in the stored incident frame."
    rows = [
        ["Field", "Information"],
        ["Incident ID", f"RW-ACC-{incident_id:05d}"],
        ["Incident Type", "Road Traffic Accident - Hit-and-Run Review Required"],
        ["Date", detected.strftime("%d-%b-%Y")],
        ["Time", f"{detected.strftime('%H:%M:%S')} IST"],
        ["Location", f"GPS {item['latitude']:.6f}, {item['longitude']:.6f}"],
        ["Detection Source", "Driver camera / uploaded video"],
        ["Reporting Vehicle", item["driver_id"]],
        ["Accident Confidence", f"{item['confidence']:.1%}"],
        ["Severity", item["severity"]],
        ["License Plate Evidence", plate_summary],
        ["Recommended Action", "Dispatch traffic officer and verify video evidence, plate crop, and GPS location before enforcement or emergency action."],
    ]
    table = Table(rows, colWidths=[48 * mm, 126 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172b4d")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#eff6ff")), ("ROWBACKGROUNDS", (1, 1), (1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([table, Spacer(1, 8 * mm), Paragraph("Evidence frame", styles["Heading3"])])
    evidence_name = Path(item.get("evidence_path") or "").name
    evidence_file = ACCIDENT_EVIDENCE_DIR / evidence_name
    if evidence_file.exists():
        image = PdfImage(str(evidence_file), width=160 * mm, height=90 * mm, kind="proportional")
        story.append(image)
    story.extend([Spacer(1, 5 * mm), Paragraph("This report is generated from automated video analysis. The reported severity, plate region, and incident classification are decision-support indicators and must be verified by an authorized officer.", styles["BodyText"])])
    document.build(story)
    return FileResponse(report_path, media_type="application/pdf", filename=f"RoadWatch_Accident_Report_{incident_id}.pdf")


@app.patch("/api/infrastructure-defects/{defect_id}")
def update_infrastructure_defect(defect_id: int, update: DefectUpdate) -> dict[str, Any]:
    allowed_statuses = {"Detected", "In progress", "Solved"}
    if update.status is not None and update.status not in allowed_statuses:
        raise HTTPException(status_code=422, detail="Status must be Detected, In progress, or Solved.")
    if update.deadline is not None:
        try:
            datetime.fromisoformat(update.deadline)
        except ValueError as error:
            raise HTTPException(status_code=422, detail="Deadline must be an ISO date or date-time.") from error
    with db_lock, database() as connection:
        existing = connection.execute("SELECT * FROM infrastructure_defects WHERE id = ?", (defect_id,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="Infrastructure defect not found")
        status = update.status if update.status is not None else existing["status"]
        deadline = update.deadline if update.deadline is not None else existing["deadline"]
        connection.execute(
            "UPDATE infrastructure_defects SET status = ?, deadline = ?, updated_at = ? WHERE id = ?",
            (status, deadline, now(), defect_id),
        )
        row = connection.execute("SELECT * FROM infrastructure_defects WHERE id = ?", (defect_id,)).fetchone()
    return dict(row)


@app.get("/api/traffic-analysis")
def traffic_analysis_events() -> dict[str, Any]:
    with db_lock, database() as connection:
        events = [dict(row) for row in connection.execute("SELECT * FROM traffic_analysis_events ORDER BY detected_at DESC LIMIT 200")]
        routes = {row["bus_number"]: dict(row) for row in connection.execute("SELECT bus_number, source, destination FROM buses")}
        priority_queue = [dict(row) for row in connection.execute(
            """SELECT * FROM traffic_analysis_events
               ORDER BY CASE density WHEN 'High' THEN 2 WHEN 'Moderate' THEN 1 ELSE 0 END DESC,
                        priority DESC, detected_at DESC LIMIT 10"""
        )]
    by_driver: dict[str, list[dict[str, Any]]] = {}
    for event in reversed(events):
        by_driver.setdefault(event["driver_id"], []).append(event)
    route_patterns = []
    for driver_id, history in by_driver.items():
        latest = history[-1]
        route_patterns.append({
            "driver_id": driver_id,
            "origin": {"latitude": history[0]["latitude"], "longitude": history[0]["longitude"]},
            "latest_location": {"latitude": latest["latitude"], "longitude": latest["longitude"]},
            "samples": len(history),
            "average_vehicles": round(sum(item["total_vehicles"] for item in history) / len(history), 1),
            "estimated_delay_minutes": max(item["estimated_delay_minutes"] for item in history),
            "density": max((item["density"] for item in history), key=lambda value: {"Low": 0, "Moderate": 1, "High": 2}.get(value, 0)),
        })
    route_patterns.sort(key=lambda item: item["estimated_delay_minutes"], reverse=True)
    forecasts = [build_congestion_forecast(driver_id, history, routes.get(driver_id)) for driver_id, history in by_driver.items()]
    forecasts.sort(key=lambda item: ({"High": 2, "Moderate": 1, "Low": 0}[item["projections"][-1]["density"]], item["projections"][-1]["estimated_vehicles"]), reverse=True)
    return {
        "events": events, "priority_queue": priority_queue,
        "route_patterns": route_patterns, "forecasts": forecasts,
        "method_note": "Forecasts use the latest 6 GPS-linked camera observations and a bounded vehicle-count trend. They are congestion estimates, not verified road speeds or guaranteed travel times.",
    }
