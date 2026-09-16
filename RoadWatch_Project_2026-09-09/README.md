# RoadWatch GIS

Local driver and government dashboard using the provided `yolo26n.pt` model, Ultralytics YOLO, and Roboflow Supervision.

## Start

Open PowerShell in this folder and run:

```powershell
.\start-dashboard.ps1
```

Open one of these Cloudflare-friendly routes in a browser:

- Driver dashboard: `http://127.0.0.1:8000/driver`
- Government GIS dashboard: `http://127.0.0.1:8000/government`

## Included workflows

- Driver dashboard: uploads a video or accesses the browser camera, keeps source video playback smooth while it sends 960px-or-smaller sampled frames to YOLO, and draws Supervision-classified bounding boxes on the live video.
- Location: **Get current location** requests browser permission and sends the driver's coordinates to the local service.
- Government dashboard: maps reported driver locations with OpenStreetMap, displays vehicle/pedestrian scene counts, and flags possible local delay using a clearly labelled vehicle-density heuristic.
- Alerts: pedestrian-and-vehicle scenes and high pedestrian/vehicle density generate safety alerts. They are indicators that require operational verification.
- Dual-model inference: `yolo26n.pt` detects general road users in real time. `models/YOLOv8_Small_RDD.pt` is the RoadDamageDetection YOLOv8-small checkpoint and scans independently for longitudinal cracks, transverse cracks, alligator cracks, and potholes.
- Performance coordination: object inference always runs first. Road-damage inference uses the same single inference lock and runs only once every 3 seconds per driver, preventing concurrent GPU/CPU contention and duplicate boxes.

## Accuracy

The supplied `yolo26n.pt` is a general COCO model. It can detect the 80 COCO classes, but no model is perfect in every road, lighting, weather, camera-angle, or local-vehicle condition. It does **not** identify school children, read license plates, prove hit-and-run events, determine road-surface condition, or measure real traffic delay from one camera scene. For those functions, add dedicated child/crosswalk, licence-plate-detection + OCR, incident-tracking, road-defect, and traffic-speed models, then validate them on a held-out labelled dataset from the target area. Adjust the confidence slider to trade recall for fewer false positives.

The road-damage model is trained for the four CRDDC2022 damage classes listed above. Validate and calibrate it on locally labelled road imagery before using its results for maintenance dispatch or safety decisions.
