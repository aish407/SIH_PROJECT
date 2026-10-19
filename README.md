# 🚦 MovIqSense

### AI-Powered Intelligent Road Monitoring & Mobility Intelligence Platform

> **Turning everyday vehicle cameras into intelligent road-sensing systems.**

MovIqSense is an **AI-powered road monitoring and mobility intelligence platform** designed to transform vehicles such as buses and other road-going vehicles into **mobile sensing units**.

The system uses **Ultralytics YOLO**, **Roboflow Supervision**, and a dedicated **Road Damage Detection model** to analyze road scenes in real time, detect road users and road defects, identify potentially unsafe situations, and communicate location-based insights through separate **Driver** and **Government GIS dashboards**.  

---

# 🎯 Problem

Traditional road monitoring systems often depend on:

* Fixed CCTV infrastructure
* Manual road inspections
* Limited geographic coverage
* Expensive dedicated sensing infrastructure
* Delayed reporting of road defects
* Fragmented traffic and safety information

This makes it difficult for authorities to continuously understand what is happening across a large road network.

### 💡 Our Approach

Instead of installing expensive sensors everywhere, **MovIqSense turns participating vehicles into mobile road-sensing units**.

A vehicle camera can continuously observe its surroundings while lightweight AI models process sampled frames and send relevant intelligence to a centralized dashboard.

---

# 🚀 What MovIqSense Does

MovIqSense combines **computer vision + geolocation + GIS visualization** into one platform.

### 👨‍✈️ Driver Side

The driver dashboard can:

* 🎥 Upload and analyze road videos
* 📷 Access the browser camera
* 🚗 Detect road users in real time
* 🧍 Detect pedestrians and vehicles
* 🛣️ Detect road-damage categories
* 📍 Capture the driver's current location
* ⚠️ Generate safety indicators
* 📊 Display real-time detection information

### 🏛️ Government Side

The government dashboard can:

* 🗺️ Visualize reported driver locations
* 📍 Display location-based road intelligence
* 🚗 Track vehicle scene counts
* 🧍 Track pedestrian scene counts
* 🚦 Identify high-density road scenes
* ⚠️ Surface potential safety situations
* 📊 Provide an operational overview of road conditions

---

# 🧠 AI Architecture

MovIqSense uses a **dual-model computer vision pipeline**.

```text
                    ┌─────────────────────┐
                    │   Vehicle Camera    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Frame Sampling      │
                    │ ≤ 960px             │
                    └──────────┬──────────┘
                               │
                               ▼
                 ┌──────────────────────────┐
                 │     Inference Lock       │
                 └────────────┬─────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
      ┌─────────────────┐          ┌────────────────────┐
      │ YOLO26n         │          │ YOLOv8 Small RDD   │
      │ General Objects │          │ Road Damage Model   │
      └────────┬────────┘          └──────────┬─────────┘
               │                              │
               ▼                              ▼
       Vehicles / People              Cracks / Potholes
               │                              │
               └──────────────┬───────────────┘
                              ▼
                    ┌─────────────────────┐
                    │ Supervision Layer   │
                    │ Bounding Boxes      │
                    │ Object Processing   │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             Driver Dashboard      Government GIS
```

---

# 🤖 AI Models

## 1. YOLO26n — Real-Time Road User Detection

The supplied `yolo26n.pt` model is used as the primary real-time object detector.

It can detect the standard **COCO object classes**, including road-relevant objects such as:

* 🚗 Cars
* 🚌 Buses
* 🚚 Trucks
* 🏍️ Motorcycles
* 🚲 Bicycles
* 🧍 People

The lightweight model is used to maintain responsive real-time inference.

---

## 2. YOLOv8 Small — Road Damage Detection

MovIqSense additionally uses:

```text
models/YOLOv8_Small_RDD.pt
```

This model independently detects four road-damage categories:

| Class              | Description                                    |
| ------------------ | ---------------------------------------------- |
| Longitudinal Crack | Cracks running along the road                  |
| Transverse Crack   | Cracks crossing the road direction             |
| Alligator Crack    | Network-like interconnected cracking           |
| Pothole            | Depressions / damaged sections of road surface |

This allows general road-user detection and road-condition detection to operate as **separate specialized AI tasks**.

---

# ⚡ Performance Optimization

Running multiple AI models simultaneously can cause unnecessary GPU/CPU contention.

MovIqSense therefore coordinates inference through a **single inference lock**.

### Inference Strategy

```text
Incoming Frame
      │
      ▼
YOLO26n Object Detection
      │
      ▼
Road-user results
      │
      └──────► Every ~3 seconds
                     │
                     ▼
             Road Damage Model
                     │
                     ▼
             Damage results
```

### Why?

Instead of running both models concurrently:

* Object detection gets priority
* Road-damage inference runs periodically
* Duplicate inference contention is reduced
* CPU/GPU resources are used more efficiently
* The source video remains smoother

---

# 🎥 Smooth Video + AI Inference

A key design decision in MovIqSense is separating:

### 🎬 Video Playback

from

### 🧠 AI Processing

The original video is kept smooth for the driver while **sampled frames** are sent to the AI pipeline.

```text
Original Video
      │
      ├──────────────► Smooth Browser Playback
      │
      ▼
Sample Frames
      │
      ▼
Resize ≤ 960px
      │
      ▼
YOLO Inference
      │
      ▼
Detection Results
```

This reduces unnecessary computation while preserving a responsive user experience.

---

# 📍 Location Intelligence

The driver dashboard provides:

### `Get Current Location`

The browser requests location permission and sends the driver's coordinates to the local service.

The government dashboard can then visualize reported driver positions on a map.

### Location Flow

```text
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
```

---

# 🗺️ Government GIS Dashboard

The government interface provides a centralized view of road intelligence.

It combines:

* 📍 Driver locations
* 🚗 Vehicle counts
* 🧍 Pedestrian counts
* ⚠️ Safety indicators
* 🚦 Vehicle-density indicators
* 🗺️ OpenStreetMap visualization

This can help authorities identify **locations requiring further operational investigation**.

---

# 🚨 Intelligent Safety Alerts

MovIqSense can surface situations such as:

### Pedestrian + Vehicle Presence

A scene containing both pedestrians and vehicles can generate a safety indicator.

### High Density

A high concentration of detected road users can generate a potential congestion/delay indicator.

> ⚠️ These are **AI-generated indicators, not definitive conclusions**. Operational verification is required before using them for enforcement, traffic control, or maintenance decisions.

---

# 📊 Traffic Density Heuristic

MovIqSense uses a clearly labelled **vehicle-density heuristic** to identify potentially delayed/high-density scenes.

Conceptually:

```text
Detected Vehicles
        +
Scene Observation
        ↓
Vehicle Density Estimate
        ↓
Threshold Evaluation
        ↓
Potential Delay Indicator
```

This is intentionally treated as an **indicator rather than a direct measurement of traffic speed or travel time**.

A single camera scene cannot reliably establish actual traffic delay without additional information such as:

* Vehicle trajectories
* Camera calibration
* GPS movement
* Speed estimation
* Multi-frame tracking
* Historical traffic data

---

# 🧩 Technology Stack

| Layer                   | Technology                   |
| ----------------------- | ---------------------------- |
| AI Detection            | Ultralytics YOLO             |
| Road Damage Detection   | YOLOv8 Small RDD             |
| Computer Vision         | OpenCV                       |
| Detection Visualization | Roboflow Supervision         |
| Mapping                 | OpenStreetMap                |
| Frontend                | Browser-based Dashboard      |
| Backend                 | Local Python Service         |
| Video Processing        | OpenCV / Browser Video       |
| Location                | Browser Geolocation API      |
| GIS                     | Interactive Map Dashboard    |
| Deployment / Tunneling  | Cloudflare-compatible routes |

---

# 📁 Project Structure

```text
MovIqSense/
│
├── models/
│   └── YOLOv8_Small_RDD.pt
│
├── assets/
│   ├── driver-dashboard.png
│   ├── government-dashboard.png
│   ├── ai-detection.png
│   └── architecture.png
│
├── yolo26n.pt
│
├── start-dashboard.ps1
│
├── app/
│   ├── ...
│   └── ...
│
├── requirements.txt
│
└── README.md
```

> Adjust the `app/` structure above to match your actual repository folders/files.

---

# 🛠️ Installation & Setup

## 1. Clone the Repository

```powershell
git clone <YOUR_REPOSITORY_URL>
cd MovIqSense
```

---

## 2. Install Dependencies

If your repository contains `requirements.txt`:

```powershell
pip install -r requirements.txt
```

---

## 3. Verify Model Files

Make sure the following files are available:

```text
yolo26n.pt
models/YOLOv8_Small_RDD.pt
```

---

# ▶️ Start MovIqSense

Open PowerShell inside the project directory:

```powershell
.\start-dashboard.ps1
```

The local service will start on:

```text
http://127.0.0.1:8000
```

---

# 🌐 Dashboards

### 🚗 Driver Dashboard

```text
http://127.0.0.1:8000/driver
```

The driver can:

1. Upload a road video
2. Start browser-camera analysis
3. View AI detections
4. Adjust confidence threshold
5. Share current location
6. Observe safety indicators

---

### 🏛️ Government GIS Dashboard

```text
http://127.0.0.1:8000/government
```

The government dashboard provides:

1. Driver-location visualization
2. Road-user statistics
3. Pedestrian/vehicle scene information
4. Potential density indicators
5. Safety alerts
6. Map-based road intelligence

---

# ☁️ Cloudflare-Friendly Access

The application is designed so the local service can be exposed through a Cloudflare-compatible tunnel when required.

This allows demonstrations from another device without deploying the complete application to a public cloud environment.

> For production deployment, authentication, HTTPS, access control, rate limiting, and secure data handling should be implemented.

---

# 🎯 Key Innovations

## 1. 🚌 Vehicles as Mobile Sensors

Instead of depending exclusively on fixed CCTV infrastructure, vehicles can become **mobile sensing units**.

---

## 2. 🧠 Dual AI Model Architecture

General road-user detection and specialized road-damage detection are handled by separate models.

```text
General Vision Model
        +
Specialized Road Model
        ↓
Combined Road Intelligence
```

---

## 3. ⚡ Resource-Aware Inference

The system avoids running computationally expensive road-damage inference on every frame.

This enables a practical balance between:

**Real-time responsiveness ↔ AI detection capability**

---

## 4. 📍 Location-Aware Intelligence

AI detections become more useful when associated with geographic context.

```text
Detection
   +
Location
   +
Timestamp
   ↓
Geospatial Road Intelligence
```

---

## 5. 🗺️ Driver → Government Intelligence Pipeline

```text
                     DRIVER
                       │
                Camera / Video
                       │
                       ▼
                 AI Inference
                       │
            ┌──────────┴──────────┐
            │                     │
       Road Users            Road Damage
            │                     │
            └──────────┬──────────┘
                       │
                 Location Data
                       │
                       ▼
                 LOCAL SERVICE
                       │
                       ▼
               GOVERNMENT GIS
                       │
                       ▼
             OPERATIONAL INSIGHT
```

---

# 📈 Potential Real-World Applications

MovIqSense can be extended for:

* 🛣️ Road maintenance monitoring
* 🕳️ Pothole reporting
* 🚦 Traffic observation
* 🚶 Pedestrian safety monitoring
* 🚌 Smart public transport
* 🏙️ Smart-city infrastructure
* 📍 Geographic road-condition mapping
* 🚧 Roadwork monitoring
* 🌧️ Waterlogging detection
* 📊 Municipal road analytics

---

# 🔮 Future Enhancements

### Advanced Computer Vision

* Dedicated pedestrian/child detection
* Crosswalk detection
* Traffic-sign recognition
* Waterlogging detection
* Lane/road-divider detection
* Road-condition segmentation

### Vehicle Intelligence

* License-plate detection + OCR
* Vehicle tracking
* Multi-object tracking
* Incident trajectory analysis
* Wrong-way detection

### Traffic Intelligence

* Speed estimation
* Average travel-time estimation
* Multi-camera vehicle tracking
* Historical congestion analysis
* Traffic-flow prediction

### AI + GIS

* Road-damage heatmaps
* Automatic maintenance prioritization
* Geographic clustering of defects
* Historical road-condition trends
* Route-level analytics

### Infrastructure

* Cloud deployment
* Authentication
* Role-based government access
* Database-backed incident storage
* Edge AI deployment
* Model monitoring and drift detection

---

# 🔐 Accuracy & Responsible AI

The supplied `yolo26n.pt` is a **general COCO object-detection model**.

Although it can detect standard COCO classes, it is not specifically trained to:

* Identify school children
* Read license plates
* Prove hit-and-run incidents
* Determine road-surface quality
* Measure actual traffic delay from a single camera scene

Similarly, the road-damage model should be **validated and calibrated against locally labelled road imagery** before its predictions are used for maintenance dispatch or safety-critical decisions.

Model performance can vary depending on:

* Lighting
* Weather
* Camera angle
* Image quality
* Vehicle speed
* Occlusion
* Road type
* Local vehicle characteristics

The confidence threshold can be adjusted to balance:

**Higher recall ↔ fewer false positives**

---

# 🧪 Recommended Validation

Before real-world deployment, evaluate the system on a **held-out dataset collected from the target geographic area**.

Useful metrics include:

```text
Precision
Recall
mAP@50
mAP@50:95
FPS
Inference Latency
False Positive Rate
False Negative Rate
```

For road-damage detection, evaluate each damage category independently.

For traffic analytics, validate predictions against ground-truth measurements such as:

* Actual vehicle counts
* GPS speed
* Traffic-camera observations
* Travel time
* Manually labelled road conditions

---

# 🏆 Why MovIqSense?

MovIqSense is not simply a video object detector.

It combines:

```text
Computer Vision
       +
Road Damage Detection
       +
Geolocation
       +
GIS
       +
Safety Indicators
       +
Government Dashboard
```

into a single **mobile road-intelligence ecosystem**.

### From:

> **"A camera sees the road."**

### To:

> **"A distributed fleet of vehicles continuously generates actionable road intelligence."**

---

# 👥 Target Users

### 🚗 Drivers / Fleet Operators

Receive real-time visual intelligence and safety indicators.

### 🏛️ Municipal & Government Authorities

Visualize geographically distributed road observations.

### 🚍 Public Transport Operators

Use buses as mobile sensing platforms.

### 🛣️ Road Maintenance Teams

Identify locations requiring road-condition verification.

### 🏙️ Smart City Teams

Integrate road observations into broader urban mobility systems.

---

# 📌 Project Status

| Component                   | Status        |
| --------------------------- | ------------- |
| Driver Dashboard            | ✅ Implemented |
| Government GIS Dashboard    | ✅ Implemented |
| YOLO Object Detection       | ✅ Implemented |
| Road Damage Detection       | ✅ Implemented |
| Browser Camera              | ✅ Implemented |
| Video Upload                | ✅ Implemented |
| Geolocation                 | ✅ Implemented |
| OSM Mapping                 | ✅ Implemented |
| Safety Indicators           | ✅ Implemented |
| Density Heuristic           | ✅ Implemented |
| Advanced Vehicle Tracking   | 🔄 Future     |
| License Plate OCR           | 🔄 Future     |
| Speed Estimation            | 🔄 Future     |
| Cloud Production Deployment | 🔄 Future     |

---

# 🚀 Quick Start

```powershell
# Clone
git clone <YOUR_REPOSITORY_URL>

# Enter project
cd MovIqSense

# Install dependencies
pip install -r requirements.txt

# Start dashboard
.\start-dashboard.ps1
```

Then open:

```text
Driver:
http://127.0.0.1:8000/driver

Government:
http://127.0.0.1:8000/government
```

---

# 📜 License

Add your project's license here.

For example:

```text
MIT License
```

---

# 💡 Vision

> **MovIqSense aims to build a scalable, AI-driven road intelligence network where vehicles become mobile sensors and every journey can contribute to safer, smarter, and more responsive cities.**

---

<p align="center">

### 🚦 MovIqSense

**Sense the Road. Understand the City. Improve Mobility.**

</p>
