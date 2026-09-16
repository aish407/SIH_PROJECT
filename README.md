🚦 MovIqSense

AI-Powered Intelligent Road Monitoring & Mobility Intelligence Platform

Turning everyday vehicle cameras into intelligent road-sensing systems.

MovIqSense is an AI-powered road monitoring and mobility intelligence platform designed to transform vehicles such as buses and other road-going vehicles into mobile sensing units.

The platform combines Ultralytics YOLO, Roboflow Supervision, a specialized Road Damage Detection model, geolocation, and GIS visualization to generate location-aware road intelligence through separate Driver and Government dashboards.

🖼️ Project Preview

🚗 Driver Dashboard

<p align="center">
  <img src="assets/driver-dashboard.png" width="92%" alt="MovIqSense Driver Dashboard">
</p>

Real-time road-user detection with sampled-frame inference and Supervision-based visualization.

🏛️ Government GIS Dashboard

<p align="center">
  <img src="assets/government-dashboard.png" width="92%" alt="MovIqSense Government GIS Dashboard">
</p>

Location-aware visualization of reported drivers, road-user counts, safety indicators, and potential traffic-density indicators.

🤖 AI Detection

<p align="center">
  <img src="assets/ai-detection.png" width="92%" alt="MovIqSense AI Detection">
</p>

🎯 Problem

Traditional road monitoring often depends on fixed CCTV infrastructure and manual inspections. This can result in:

Limited geographic coverage

Expensive sensing infrastructure

Delayed road-defect reporting

Fragmented traffic information

Difficulty monitoring large road networks continuously

💡 Our Approach

MovIqSense turns participating vehicles into mobile road-sensing units.

Vehicle cameras observe the road while lightweight AI models process sampled frames and produce road-user and road-condition intelligence. Relevant information can then be visualized geographically for government and operational teams.

🚀 Core Features

Feature

Description

🎥 Video Analysis

Upload a road video and analyze sampled frames

📷 Browser Camera

Analyze live camera input from the browser

🚗 Object Detection

Detect vehicles, pedestrians and other COCO objects

🛣️ Road Damage Detection

Detect cracks and potholes using a dedicated RDD model

📍 Driver Location

Capture browser-provided latitude and longitude

🗺️ GIS Dashboard

Visualize reported driver locations using OpenStreetMap

🚨 Safety Alerts

Surface pedestrian/vehicle and high-density indicators

📊 Scene Analytics

Display vehicle and pedestrian counts

⚡ Performance Control

Coordinate two AI models through a single inference lock

🎚️ Confidence Control

Adjust detection confidence to trade recall for fewer false positives

🧠 AI Architecture

                         ┌──────────────────────┐
                         │    Vehicle Camera    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Frame Sampling     │
                         │     ≤ 960 px         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Inference Lock    │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    │                                │
                    ▼                                ▼
          ┌───────────────────┐          ┌────────────────────┐
          │     YOLO26n       │          │ YOLOv8 Small RDD   │
          │ General Detection │          │ Road Damage Model  │
          └─────────┬─────────┘          └──────────┬─────────┘
                    │                                │
                    ▼                                ▼
            Vehicles / People                Cracks / Potholes
                    │                                │
                    └──────────────┬─────────────────┘
                                   ▼
                         ┌──────────────────────┐
                         │ Roboflow Supervision │
                         │ Boxes + Processing   │
                         └──────────┬───────────┘
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
                Driver Dashboard        Government GIS
                       │                         │
                       └────────────┬────────────┘
                                    ▼
                           Road Intelligence

🤖 AI Models

1. YOLO26n — Real-Time Road User Detection

The supplied yolo26n.pt model is the primary real-time object detector.

It can detect standard COCO classes, including road-relevant objects such as:

🚗 Car

🚌 Bus

🚚 Truck

🏍️ Motorcycle

🚲 Bicycle

🧍 Person

The lightweight model is used to keep inference responsive during video/camera analysis.

2. YOLOv8 Small — Road Damage Detection

The project additionally uses:

models/YOLOv8_Small_RDD.pt

The model detects four Road Damage Detection categories:

Class

Description

Longitudinal Crack

Cracks running along the road

Transverse Crack

Cracks crossing the road direction

Alligator Crack

Interconnected network-like cracking

Pothole

Depressed/damaged road sections

⚡ Performance-Aware Dual Inference

Running multiple models concurrently can create unnecessary CPU/GPU contention.

MovIqSense therefore coordinates inference through a single inference lock.

Strategy

Incoming Frame
      │
      ▼
YOLO26n Object Detection
      │
      ├──────────────► Vehicle / Pedestrian Results
      │
      └── Every ~3 seconds
                    │
                    ▼
            Road Damage Model
                    │
                    ▼
            Damage Results

Object inference runs first. Road-damage inference runs periodically using the same inference lock.

This helps:

Prevent concurrent model execution

Reduce CPU/GPU contention

Avoid duplicate processing

Preserve smoother source-video playback

🎥 Smooth Video + AI Processing

MovIqSense separates video playback from AI inference.

                 Original Video
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
      Smooth Playback       Sampled Frames
                                 │
                                 ▼
                           Resize ≤ 960 px
                                 │
                                 ▼
                            AI Inference
                                 │
                                 ▼
                         Detection Results

Instead of sending every full-resolution frame to the AI pipeline, sampled frames are resized and processed.

This provides a practical balance between:

Real-time responsiveness ↔ AI processing capability

📍 Location Intelligence

The Driver Dashboard provides a Get Current Location function.

The browser requests permission and sends the driver's coordinates to the local service.

Driver Browser
      │
      ▼
Browser Geolocation API
      │
      ▼
Latitude + Longitude
      │
      ▼
Local Service
      │
      ▼
Government GIS Dashboard

🗺️ Government GIS Dashboard

The Government Dashboard combines road observations with geographic context.

It can display:

📍 Reported driver locations

🚗 Vehicle scene counts

🧍 Pedestrian scene counts

⚠️ Safety indicators

🚦 Vehicle-density indicators

🗺️ OpenStreetMap visualization

The goal is to provide a centralized operational view of distributed road observations.

🚨 Intelligent Safety Indicators

MovIqSense can generate safety indicators when:

Pedestrian + Vehicle Scene

A scene containing pedestrians and vehicles can generate a potential safety alert.

High Vehicle/Pedestrian Density

A high detected object density can generate a potential congestion/delay indicator.

Important: These are AI-generated indicators and require operational verification. They are not proof of an incident, violation, or actual traffic delay.

📊 Vehicle Density Heuristic

The platform uses a clearly labelled vehicle-density heuristic.

Detected Vehicles
        │
        ▼
Scene Density Estimate
        │
        ▼
Threshold Evaluation
        │
        ▼
Potential Delay Indicator

A single camera scene cannot reliably establish real traffic delay. Accurate traffic analytics would require additional information such as:

Vehicle trajectories

GPS movement

Speed estimation

Multi-frame tracking

Camera calibration

Historical traffic data

🧩 Technology Stack

Layer

Technology

AI Detection

Ultralytics YOLO

Road Damage

YOLOv8 Small RDD

Computer Vision

OpenCV

Detection Visualization

Roboflow Supervision

Mapping

OpenStreetMap

Location

Browser Geolocation API

Video Processing

Browser Video / OpenCV

Backend

Local Python Service

Dashboard

Web-based UI

Tunnel / Demo Access

Cloudflare-compatible setup

📁 Project Structure

MovIqSense/
│
├── assets/
│   ├── driver-dashboard.png
│   ├── government-dashboard.png
│   ├── ai-detection.png
│   └── architecture.png
│
├── models/
│   └── YOLOv8_Small_RDD.pt
│
├── yolo26n.pt
├── start-dashboard.ps1
├── requirements.txt
├── README.md
└── app/
    └── ...

Update the app/ section to match your repository's actual folder structure.

🛠️ Installation

1. Clone the Repository

git clone <YOUR_REPOSITORY_URL>
cd MovIqSense

2. Install Dependencies

pip install -r requirements.txt

3. Verify Model Files

Make sure these files exist:

yolo26n.pt
models/YOLOv8_Small_RDD.pt

▶️ Start the Dashboard

Open PowerShell in the project directory:

.\start-dashboard.ps1

The local service runs on:

http://127.0.0.1:8000

🌐 Dashboard Routes

🚗 Driver Dashboard

http://127.0.0.1:8000/driver

Driver workflow:

Upload a road video or start the browser camera

View real-time detections

Adjust confidence threshold

Capture current location

Observe safety indicators

Review detected road conditions

🏛️ Government GIS Dashboard

http://127.0.0.1:8000/government

Government workflow:

View reported driver locations

Inspect vehicle/pedestrian scene counts

Review potential density indicators

View safety alerts

Analyze road intelligence geographically

☁️ Cloudflare-Friendly Demonstration

The application is designed to work with a Cloudflare-compatible tunnel when remote demonstration is required.

This makes it possible to expose the local dashboard for testing from another device without immediately deploying the entire application to public cloud infrastructure.

For production deployment, implement:

HTTPS

Authentication

Role-based access control

Secure data handling

Rate limiting

Persistent storage

Audit logging

🎯 Innovation

1. 🚌 Vehicles as Mobile Sensors

Instead of relying only on fixed CCTV infrastructure, participating vehicles can act as mobile sensing units.

2. 🧠 Dual-Model Computer Vision

General road-user detection and specialized road-damage detection are handled by separate models.

General Vision
      +
Road Damage Vision
      ↓
Combined Road Intelligence

3. ⚡ Resource-Aware Inference

Road-damage inference is intentionally throttled instead of being executed on every frame.

4. 📍 Geospatial Intelligence

A detection becomes more operationally useful when associated with:

Detection + Location + Timestamp
              ↓
      Geospatial Intelligence

5. 🏛️ Driver → Government Pipeline

Driver Camera
     │
     ▼
AI Detection
     │
 ┌───┴─────────────┐
 ▼                 ▼
Road Users     Road Damage
 └───────┬─────────┘
         ▼
   Location Data
         │
         ▼
   Local Service
         │
         ▼
 Government GIS
         │
         ▼
Operational Insight

🌍 Potential Applications

MovIqSense can be extended to support:

🛣️ Road maintenance monitoring

🕳️ Pothole reporting

🚦 Traffic observation

🚶 Pedestrian safety monitoring

🚌 Smart public transportation

🏙️ Smart-city infrastructure

📍 Geographic road-condition mapping

🚧 Roadwork monitoring

🌧️ Waterlogging detection

📊 Municipal road analytics

🔮 Future Enhancements

Advanced Computer Vision

Dedicated child/pedestrian detection

Crosswalk detection

Traffic-sign recognition

Waterlogging detection

Road-divider detection

Road-condition segmentation

Vehicle Intelligence

License-plate detection + OCR

ByteTrack / multi-object tracking

Vehicle trajectory analysis

Wrong-way detection

Incident tracking

Traffic Intelligence

Speed estimation

Travel-time estimation

Multi-camera tracking

Historical congestion analysis

Traffic-flow prediction

AI + GIS

Road-damage heatmaps

Geographic clustering

Maintenance prioritization

Historical road-condition trends

Route-level analytics

Production Infrastructure

Cloud deployment

Authentication

Government role-based access

Database-backed incident storage

Edge AI deployment

Model monitoring and drift detection

🔐 Accuracy & Responsible AI

The supplied yolo26n.pt is a general COCO object-detection model.

It does not inherently:

Identify school children

Read license plates

Prove hit-and-run events

Determine road-surface condition

Measure actual traffic delay from one camera scene

The road-damage model should also be validated and calibrated against locally labelled road imagery before its predictions are used for maintenance dispatch or safety-critical decisions.

Performance can vary with:

Lighting

Weather

Camera angle

Image quality

Vehicle speed

Occlusion

Road type

Local scene characteristics

The confidence threshold can be adjusted to balance:

Higher recall ↔ fewer false positives

🧪 Recommended Validation

Before real-world deployment, evaluate the system on a held-out dataset representing the target area.

Recommended metrics:

Precision
Recall
mAP@50
mAP@50:95
FPS
Inference Latency
False Positive Rate
False Negative Rate

For road damage, evaluate each damage category independently.

For traffic analytics, compare predictions against ground truth such as:

Actual vehicle counts

GPS speed

Traffic-camera observations

Travel time

Manually labelled road conditions

📌 Project Status

Component

Status

Driver Dashboard

✅ Implemented

Government GIS Dashboard

✅ Implemented

YOLO Object Detection

✅ Implemented

Road Damage Detection

✅ Implemented

Browser Camera

✅ Implemented

Video Upload

✅ Implemented

Geolocation

✅ Implemented

OpenStreetMap Mapping

✅ Implemented

Safety Indicators

✅ Implemented

Density Heuristic

✅ Implemented

Advanced Tracking

🔄 Planned

License Plate OCR

🔄 Planned

Speed Estimation

🔄 Planned

Cloud Production Deployment

🔄 Planned

🏆 Project Vision

MovIqSense aims to build a scalable AI-driven road intelligence network where vehicles become mobile sensors and every journey can contribute to safer, smarter, and more responsive cities.

🚦 Sense the Road. Understand the City. Improve Mobility.

📜 License

Add your preferred project license here, for example:

MIT License
