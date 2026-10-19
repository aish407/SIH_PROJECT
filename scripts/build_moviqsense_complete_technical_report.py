from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "docs" / "MovIqSense_Complete_SIH_2026_Technical_Report.docx"
NAVY, BLUE, PALE, TEXT, BORDER, GREY = "132238", "1F4E79", "F5F9FC", "1F2937", "D9E2F3", "667085"


def run(para, text, bold=False, size=10.1, color=TEXT):
    r = para.add_run(text)
    r.bold = bold
    r.font.name = "Aptos"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    return r


def cell_style(cell, shade="FFFFFF"):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), shade)
    tcpr.append(shd)
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "6")
        edge.set(qn("w:color"), BORDER)
        borders.append(edge)
    tcpr.append(borders)
    margins = OxmlElement("w:tcMar")
    for side in ("top", "start", "bottom", "end"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:w"), "105")
        edge.set(qn("w:type"), "dxa")
        margins.append(edge)
    tcpr.append(margins)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def para(doc, text, size=10.1, after=5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.12
    run(p, text, size=size)
    return p


def lead(doc, label, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.12
    run(p, label + " ", bold=True)
    run(p, text)
    return p


def bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.02
    run(p, text, size=9.6)
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.space_before = Pt(8 if level == 1 else 5)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Aptos Display"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    r.font.size = Pt(14 if level == 1 else 11.4)
    r.font.color.rgb = RGBColor(0, 0, 0)
    return p


def table(doc, headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    t.style = "Table Grid"
    header_properties = t.rows[0]._tr.get_or_add_trPr()
    repeating_header = OxmlElement("w:tblHeader")
    repeating_header.set(qn("w:val"), "true")
    header_properties.append(repeating_header)
    for i, text in enumerate(headers):
        c = t.rows[0].cells[i]
        c.width = Inches(widths[i])
        cell_style(c, NAVY)
        run(c.paragraphs[0], text, bold=True, color="FFFFFF", size=8.55)
    for index, values in enumerate(rows):
        cells = t.add_row().cells
        for i, text in enumerate(values):
            c = cells[i]
            c.width = Inches(widths[i])
            cell_style(c, "FFFFFF" if index % 2 == 0 else PALE)
            c.paragraphs[0].paragraph_format.space_after = Pt(0)
            run(c.paragraphs[0], str(text), size=8.35)
    gap = doc.add_paragraph()
    gap.paragraph_format.space_after = Pt(1)
    return t


def page_break(doc):
    doc.add_page_break()


def compact_source(doc, source):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    run(p, source, size=8.5, color=GREY)


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.58)
    section.bottom_margin = Inches(0.56)
    section.left_margin = Inches(0.67)
    section.right_margin = Inches(0.67)
    doc.styles["Normal"].font.name = "Aptos"
    doc.styles["Normal"].font.size = Pt(10.1)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(footer, "MovIqSense | SIH 2026 | Problem Statement 26124 | Technical submission report", size=8.1, color=GREY)

    # 1 Cover
    for _ in range(5):
        doc.add_paragraph()
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = title.add_run("MovIqSense")
    rr.bold = True
    rr.font.name = "Aptos Display"
    rr._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
    rr._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    rr.font.size = Pt(34)
    rr.font.color.rgb = RGBColor(0, 0, 0)
    s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(s, "Complete Technical and Implementation Report", bold=True, size=17, color=BLUE)
    s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(s, "AI Powered Mobile Urban Intelligence Platform Using Public Transport Fleet", size=12)
    for _ in range(4): doc.add_paragraph()
    table(doc, ["Submission detail", "Value"], [
        ["Problem Statement", "SIH 2026 Problem Statement 26124"],
        ["Organisation", "Bharat Electronics Limited"],
        ["Theme and category", "Smart Automation | Software"],
        ["Project purpose", "Transform public buses into mobile sensing units for road safety, road condition and urban traffic intelligence."],
        ["Report scope", "System design, implementation plan, cost control, governance, pilot design, risks, impact and commercial path."],
        ["Prepared for", "Smart India Hackathon evaluation and discussion with prospective public-sector pilot partners."],
    ], [2.15, 5.35])
    page_break(doc)

    # 2 Executive brief
    heading(doc, "1 Executive Brief")
    para(doc, "MovIqSense converts a bus from a passive recording asset into a mobile observation point. A road-facing camera is analysed near the source, GPS tags the meaningful observations, and a government dashboard groups them into road-defect, traffic, safety and incident workflows. The design does not ask authorities to install a new fixed camera at every road. It uses the daily movement of public buses to extend coverage across many corridors.")
    para(doc, "The project addresses a practical operations gap. Road defects, waterlogging, unsafe pedestrian conditions and traffic build-up are often discovered through scheduled inspection, fixed CCTV coverage or citizen complaints. Those channels remain useful, but they are delayed or geographically limited. MovIqSense adds a repeatable field signal that can be verified, prioritised and routed to the responsible authority.")
    table(doc, ["Decision area", "MovIqSense response", "What remains human controlled"], [
        ["Road observation", "Video models identify candidate potholes, waterlogging, road damage, signs, zebra crossings and divider conditions.", "Field verification and work-order approval."],
        ["Traffic intelligence", "Vehicle class counts, density indicators, route-level observations and delay heuristics are presented on GIS.", "Traffic intervention and policy decisions."],
        ["Incident evidence", "Accident cues, vehicle track context, plate-crop evidence, timestamp and GPS are retained for authorised review.", "Police investigation, enforcement and legal conclusion."],
        ["Fleet platform", "Bus identity, online status, source-destination, camera health and live observations are consolidated.", "Fleet operations and data-retention policy."],
    ], [1.4, 3.55, 2.55])
    lead(doc, "Submission position.", "The prototype demonstrates the end-to-end chain from video to geo-tagged event to government action. Deployment claims are intentionally conditional on field validation, camera compatibility, authority approvals and local model evaluation.")
    page_break(doc)

    # 3 problem and evidence
    heading(doc, "2 Problem Context and National Relevance")
    para(doc, "Indian cities need timely information about road condition and traffic safety, yet observation capacity is uneven. Fixed cameras cover selected junctions. Manual inspections cannot visit every corridor every day. Complaint systems report issues after a citizen experiences them. Public buses, by contrast, repeatedly travel roads that municipal and transport authorities already need to understand.")
    table(doc, ["Official signal", "Reported value", "Why it matters to this project"], [
        ["Road Accidents in India 2023", "4,80,583 road accidents, 1,72,890 deaths and 4,62,825 injuries reported by States and UTs.", "Supports earlier hazard visibility, safer-road evidence and faster authority review."],
        ["PM eBus Sewa", "10,000 e-buses planned under PPP; urban mobility programme includes ITMS and NCMC context.", "Creates a credible connected-city fleet environment for an intelligence layer."],
        ["PM eBus Sewa scale", "Estimated scheme cost Rs 57,613 crore with Rs 20,000 crore central support.", "Shows that public transport is an established government infrastructure and technology investment domain."],
        ["Programme progress", "As reported by the official portal in September 2026, 10,000 buses were shown across 115 cities and 26 States and UTs.", "Demonstrates a large, staged ecosystem; it is not assumed to be an automatic buyer base."],
    ], [1.55, 2.6, 3.35])
    para(doc, "The technical opportunity is not to replace inspectors, police or civic engineers. It is to give them a better queue of verified, located and time-stamped observations. That distinction matters for a government deployment: machine output should shorten the path to action, not bypass accountability.")
    page_break(doc)

    # 4 requirements traceability
    heading(doc, "3 Requirement Traceability")
    para(doc, "MovIqSense was designed against the requested problem statement rather than as a generic camera demo. Each feature has a visible link to a public-transport or government action workflow.")
    table(doc, ["Problem statement need", "Implemented or planned mechanism", "Authority outcome"], [
        ["Road hazards and defects", "Independent YOLO-compatible detectors for potholes, waterlogging, speed breakers, road dividers, traffic signs and zebra crossings; event confidence and GPS stored with evidence.", "A ranked infrastructure-defect queue for inspection and repair allocation."],
        ["Vehicle density and bottlenecks", "Object detection, class counting, multi-object tracking, density bands and route-time aggregation.", "Traffic analysis, congestion heat layers and indicative delay signals."],
        ["Pedestrian safety", "Person detection and proximity/risk rules near moving traffic; alert wording supports driver caution.", "Early warning of vulnerable-road-user situations; no automated enforcement claim."],
        ["Hit-and-run or rash driving", "Accident-event cue, tracked vehicle context, licence-plate crop model, GPS, timestamp and evidence links.", "Authorised evidence review and high-severity alert escalation."],
        ["Centralised intelligence", "FastAPI backend, event database, GIS interface, live buses, infrastructure and accident tables.", "A single operational view that joins fleet movement with road observations."],
    ], [1.65, 3.35, 2.5])
    lead(doc, "Design principle.", "Every detection enters a confidence-aware workflow. Low-confidence observations are retained for trend analysis or review, while actionable alerts require configured thresholds and temporal confirmation.")
    page_break(doc)

    # 5 architecture
    heading(doc, "4 Reference Architecture")
    para(doc, "The reference architecture separates real-time perception from central coordination. This protects video responsiveness and reduces bandwidth. The same pattern can operate as a browser-led prototype, a rugged edge-compute deployment, or a hybrid fleet architecture.")
    table(doc, ["Layer", "Primary components", "Responsibility"], [
        ["Capture", "Front, rear or side bus camera; uploaded video; optional mobile camera; GPS or AVL feed.", "Acquires visual and location signals."],
        ["Edge perception", "Ultralytics YOLO inference, OpenCV frame pipeline, object tracker, detector scheduler, evidence cropper.", "Produces bounded detections and compact structured events."],
        ["Event coordination", "FastAPI services, validation rules, SQLite prototype database or production relational store, file evidence store.", "Normalises events, stores metadata and protects workflows."],
        ["Analytics", "Route-time aggregation, density bands, hotspot clustering, defect priority score, delay heuristic.", "Converts observations into operational indicators."],
        ["Government application", "Leaflet GIS map, government dashboard, defect table, traffic table, all-buses view, PDF report endpoint.", "Supports review, status update, reporting and dispatch."],
    ], [1.25, 3.45, 2.8])
    para(doc, "The architectural boundary is deliberate: video frames should not wait for the database or dashboard; the dashboard should not need to stream raw video continuously; and authorised evidence should be opened only when an officer needs it.")
    page_break(doc)

    # 6 field capture
    heading(doc, "5 Onboard and Field Capture Design")
    para(doc, "A production pilot begins with one forward-facing road camera because it gives the highest road-condition value per unit of compute. Rear and side cameras can be added after the first corridor proves power, mounting, lighting and network assumptions. Cabin video should remain outside the road-intelligence pipeline unless a separate approved purpose, privacy policy and access protocol exist.")
    table(doc, ["Input", "Minimum pilot specification", "Rationale"], [
        ["Road camera", "Existing compatible 720p or 1080p stream; stable mount; known field of view.", "Avoids purchasing cameras before checking existing fleet assets."],
        ["Position", "Existing authorised GPS/AVL feed preferred; fallback GNSS tracker where unavailable.", "Prevents duplicate hardware and aligns data with fleet operations."],
        ["Edge compute", "CPU prototype; NVIDIA CUDA/FP16 capable device where stable multi-stream inference is required.", "Supports staged cost while retaining a path to low-latency operation."],
        ["Connectivity", "4G/5G or depot Wi-Fi; event messages first; media upload only on policy trigger.", "Avoids continuous HD video data cost."],
        ["Power and enclosure", "Vehicle-rated DC power conversion, fuse protection and vibration-aware enclosure.", "A field pilot fails if compute is treated like an office laptop."],
    ], [1.4, 3.45, 2.65])
    lead(doc, "Pilot rule.", "The team should audit camera codec, resolution, frame rate, GPS cadence and power stability on each bus before promising a model-level accuracy figure.")
    page_break(doc)

    # 7 real-time pipeline
    heading(doc, "6 Real Time Video Processing Pipeline")
    para(doc, "The live pipeline is engineered so perception remains smooth even when individual models take longer than a frame interval. Frames are decoded continuously. Inference is scheduled on selected frames, while the latest suitable detection overlay is reused on intermediate frames. This is preferable to freezing the video to wait for a detector result.")
    table(doc, ["Stage", "Method", "Output"], [
        ["Decode", "OpenCV captures frames and preserves source timing where possible.", "Consistent image stream with source metadata."],
        ["Preprocess", "Resize to model input shape, colour conversion only when required, no unnecessary copies.", "GPU or CPU ready tensor/image."],
        ["Inference", "Model loaded once; PyTorch inference_mode; CUDA FP16 only after compatibility test; configurable confidence threshold.", "Raw boxes, classes and confidence scores."],
        ["Tracking and smoothing", "Tracker ID assignment, temporal confirmation, frame skipping or reuse under load.", "Stable labels and lower duplicate-event rate."],
        ["Annotation", "Supervision-compatible labels and boxes on visible display frame.", "Readable live display and saved evidence frame."],
        ["Publish", "Event JSON plus selected crop/full-frame evidence sent to backend; processed MP4 optionally saved.", "Dashboard update without sending every raw frame."],
    ], [1.35, 3.7, 2.45])
    para(doc, "Latency, FPS, device type and confidence are exposed because a public-sector operator needs to know whether the system is operating within an acceptable envelope. These values are diagnostics, not proof of universal accuracy.")
    page_break(doc)

    # 8 model portfolio
    heading(doc, "7 Computer Vision Model Portfolio")
    para(doc, "MovIqSense uses a modular model registry. Each detector is loaded independently, scheduled according to its purpose, and reported with its own class label. This prevents a specialist road-condition model from being confused with the general vehicle model and makes it possible to disable a weak model without stopping the rest of the platform.")
    table(doc, ["Model family", "Primary role", "Operational use"], [
        ["General object detector", "Cars, buses, motorcycles, people and other common road classes.", "Vehicle count, pedestrian count, density and contextual evidence."],
        ["Pothole or road-damage detector", "Pothole candidate boxes and road-damage visual evidence.", "Infrastructure defect record and repair priority input."],
        ["Waterlogging detector", "Surface water or waterlogged-road candidate region.", "Monsoon hazard observation and corridor escalation."],
        ["Road feature detectors", "Speed breaker, divider, zebra crossing, traffic sign and related project-specific classes.", "Maintenance, visibility and safety observation workflows."],
        ["Accident and plate evidence components", "Accident cue plus vehicle/plate crop detection and tracking context.", "Authorised incident review; not automatic liability determination."],
    ], [1.7, 2.75, 3.05])
    lead(doc, "Model governance.", "A model is considered deployable only after versioning, local validation, confidence calibration, false-positive review and an accountable owner are recorded. Downloaded weights are not treated as proof of field suitability.")
    page_break(doc)

    # 9 validation plan
    heading(doc, "8 Model Validation and Quality Control")
    para(doc, "The quality question is not simply whether a box appears on a sample video. For a city pilot, the relevant question is whether the system produces sufficiently useful observations under local lighting, rain, camera angle, traffic mix and road surface conditions. MovIqSense therefore proposes a measured validation loop before an alert class is allowed to create work for field teams.")
    table(doc, ["Validation activity", "How it is measured", "Release decision"], [
        ["Local test set", "Annotated clips across day, night, rain, glare, rough roads and multiple bus speeds.", "Reject a model that has no local evidence."],
        ["Detection accuracy", "Precision, recall, F1 and confusion matrix at the actual operating threshold.", "Select threshold by operational workload, not by a marketing number."],
        ["Temporal stability", "Track persistence and repeat detection across adjacent frames and repeat bus passes.", "Reduce flicker and repeated alerts."],
        ["Location quality", "Compare event GPS with known route landmarks; record uncertainty where GPS is weak.", "Avoid an overconfident repair location."],
        ["Human review", "Officer labels sampled events as correct, useful, duplicate or irrelevant.", "Feeds model retraining and policy adjustment."],
    ], [1.55, 3.55, 2.4])
    para(doc, "Recommended pilot acceptance targets should be negotiated with the authority. A sensible example is to require a specified precision for high-priority alert classes, a stated maximum alert-to-dashboard delay, and a minimum percentage of high-priority events that can be verified with usable evidence. Those thresholds must be based on the selected corridor, not copied from an unrelated dataset benchmark.")
    page_break(doc)

    # 10 data flow
    heading(doc, "9 Data Model and Event Lifecycle")
    para(doc, "The central record is an observation event rather than an unstructured video file. The event holds enough information to be reviewed, mapped, deduplicated and connected to an authority workflow. Raw media is optional evidence with controlled retention.")
    table(doc, ["Event field", "Example", "Purpose"], [
        ["Identity", "event_id, bus_id, model_version, event_type", "Traceability and reproducibility."],
        ["Time and place", "UTC timestamp, local display time, latitude, longitude, route segment", "Maps an observation to a corridor and duty period."],
        ["Model result", "class, confidence, box coordinates, tracker_id, density metrics", "Explains what the model saw and at what confidence."],
        ["Evidence reference", "full-frame path, plate crop path, processed-video link", "Allows authorised review without embedding media in every table."],
        ["Workflow state", "detected, in progress, solved, rejected, duplicate", "Makes follow-up visible and auditable."],
        ["Verification", "reviewer, review timestamp, notes, work order reference", "Separates AI observation from verified civic action."],
    ], [1.45, 3.35, 2.7])
    lead(doc, "Data minimisation.", "The platform should transmit a compact event message first. It should upload or retain high-volume media only when policy, severity, confidence or reviewer action requires it.")
    page_break(doc)

    # 11 geo
    heading(doc, "10 GIS and Cooperative Localisation")
    para(doc, "GPS from one bus can be noisy, especially in dense urban streets. MovIqSense treats location as an estimate with context. It binds observation time, vehicle route, direction, nearby road segment and repeat reports. Where several buses report a similar defect or congestion condition, the system can form a stronger corridor-level hypothesis than a single isolated frame.")
    table(doc, ["Localisation stage", "Technique", "Confidence improvement"], [
        ["Initial fix", "GPS/AVL position at or near the detection timestamp.", "Provides first map coordinate and bus identity."],
        ["Route snapping", "Associate point with an authorised route polyline or nearby road segment.", "Limits visual drift away from the actual corridor."],
        ["Temporal alignment", "Use frame timestamp, GPS cadence and bus direction.", "Reduces mismatch caused by asynchronous telemetry."],
        ["Spatial clustering", "Group nearby, similar observations within a configurable distance/time window.", "Highlights repeated signals and reduces duplicate work orders."],
        ["Human confirmation", "Field crew or officer validates selected high-priority points.", "Produces the final maintenance-grade record."],
    ], [1.55, 3.5, 2.4])
    para(doc, "This cooperative-localisation approach is useful for potholes, waterlogging and recurring bottlenecks. It does not claim survey-grade accuracy from consumer GPS. The map should show confidence and evidence age where a decision depends on location precision.")
    page_break(doc)

    # 12 analytics
    heading(doc, "11 Traffic Analytics and Delay Estimation")
    para(doc, "Traffic density is estimated from the current scene using vehicle-class counts, tracked objects, occupancy proxy and persistence. It is a camera-scene indicator, not a direct measurement of road speed. The dashboard therefore labels delay output as an estimate or possible delay unless it is combined with validated travel-time data.")
    table(doc, ["Metric", "Computation approach", "Dashboard meaning"], [
        ["Vehicle count", "Count active tracked car, bus and motorcycle detections in the latest stable window.", "Current observed fleet mix."],
        ["Density band", "Configured low, medium or high thresholds using count, occupancy and persistence.", "Simple operational view of traffic pressure."],
        ["Route pattern", "Aggregate density observations by route segment, direction, time bucket and day type.", "Repeat congestion hotspots and peak patterns."],
        ["Delay heuristic", "Compare current density/persistence with corridor baseline; optionally combine AVL travel time later.", "Indicative normal, possible delay or high-delay signal."],
        ["Forecast horizon", "Use rolling route-time feature history for 5, 10 and 15 minute trend projections after sufficient data collection.", "A planning aid, not an unsupported real-time certainty."],
    ], [1.45, 3.7, 2.3])
    lead(doc, "Responsible interpretation.", "Forecast accuracy requires local historical data and validation. In the SIH prototype, the correct position is to show the pipeline and explain how operational data matures the forecast model over time.")
    page_break(doc)

    # 13 alerts
    heading(doc, "12 Alerting and Priority Engine")
    para(doc, "A dashboard with every possible detection becomes a noise generator. MovIqSense uses a priority score to route the most serious and reliable observations first. The score is designed to be transparent: users can see why an event is high priority rather than receiving a black-box command.")
    table(doc, ["Priority input", "Illustrative contribution", "Why it matters"], [
        ["Severity", "High for major road damage, waterlogging, collision cue or vulnerable-road-user risk.", "Aligns work with potential safety impact."],
        ["Model confidence", "Higher confidence increases score; low confidence is held for review or trend use.", "Reduces false-alert workload."],
        ["Repeat confirmation", "Multiple passes or bus reports raise confidence and priority.", "Separates persistent infrastructure issues from one-off visual artefacts."],
        ["Traffic exposure", "High density or route criticality increases priority.", "Prioritises defects that affect more road users."],
        ["Age and status", "Unresolved high-priority events age upward; solved/rejected events leave the active queue.", "Creates a visible service-management loop."],
    ], [1.6, 3.15, 2.7])
    para(doc, "For a high-severity accident cue, the government dashboard can show a prominent alert with bus number, location, time and evidence link. The alert is a prompt for authorised response. It must not state guilt, issue a fine or publish a vehicle registration number to unauthorised viewers.")
    page_break(doc)

    # 14 driver workflow
    heading(doc, "13 Driver and Fleet Operator Workflow")
    para(doc, "The driver-side application is intentionally simple. Its task is to establish bus identity, request authorised location sharing, accept an uploaded road video or camera feed, show the live annotated stream and display current safety indicators. It should not distract a moving driver. In a production rollout, an attendant, depot operator or installed edge unit should manage the system while the driver focuses on driving.")
    table(doc, ["Step", "Driver or fleet action", "System action"], [
        ["1", "Select or confirm registered bus number.", "Loads bus source, destination and approved fleet configuration."],
        ["2", "Start authorised GPS tracking or connect existing AVL feed.", "Broadcasts periodic location updates and camera-health status."],
        ["3", "Upload video for review or start permitted road-camera stream.", "Runs low-latency detector schedule and shows bounded result."],
        ["4", "Continue normal fleet operation.", "Sends material events, keeps counts and produces evidence only when needed."],
        ["5", "Stop session or hand over at depot.", "Closes stream state, finalises processed video and syncs retained events."],
    ], [0.65, 3.4, 4.05])
    lead(doc, "Safety constraint.", "The interface should be configured so that a driver is never expected to operate menus, review alerts or handle evidence while the bus is in motion.")
    page_break(doc)

    # 15 government workflow
    heading(doc, "14 Government Dashboard Facilities")
    para(doc, "The government dashboard is an operations surface rather than a visual display alone. It joins the GIS map with verified work queues. Role-based users can view only the facilities relevant to their department: fleet operations, road maintenance, traffic management or authorised incident response.")
    table(doc, ["Dashboard area", "Core facility", "Primary user"], [
        ["Live operations map", "Online buses, recent observation markers, density context and severity symbols.", "ICCC, transport control room, supervisor."],
        ["Infrastructure defects", "Pothole, waterlogging and road-feature records with location, count, evidence, status and deadline field.", "Municipal/PWD maintenance officer."],
        ["Traffic analysis", "Cars, buses, motorcycles, density, route segment and high-density top-ten queue.", "Traffic and transport planner."],
        ["All buses", "Online/offline state, source, destination, live object count and incident indication; online buses are drill-down capable.", "Fleet administrator."],
        ["Accident evidence", "Severity, location, timestamp, plate-crop evidence, incident frame and official PDF report option.", "Authorised traffic/police user."],
    ], [1.6, 3.65, 2.15])
    para(doc, "The defect workflow deliberately includes status and repair deadlines. Traffic analysis does not. Traffic is an observation stream; a pothole or waterlogging record is a maintenance case that needs ownership and closure.")
    page_break(doc)

    # 16 security
    heading(doc, "15 Security Privacy and Responsible AI")
    para(doc, "MovIqSense handles visual data, movement information and potentially sensitive incident evidence. The prototype can demonstrate the workflow, but a government pilot must implement formal security, privacy and access controls before live operational use.")
    table(doc, ["Control area", "Recommended control", "Reason"], [
        ["Authentication", "Authority-managed user identity, strong passwords or SSO, role-based access and session expiry.", "Limits operational and evidence access."],
        ["Evidence protection", "Encrypted storage, signed short-lived access links, audit log and restricted download permission.", "Protects accident and plate-crop evidence."],
        ["Data minimisation", "Send events first; retain raw video according to an approved schedule and purpose.", "Reduces unnecessary personal-data exposure and storage cost."],
        ["Model accountability", "Show model version, confidence and review state; keep human decision in the workflow.", "Prevents automated output being mistaken for final civic or legal fact."],
        ["Retention and deletion", "Authority-defined schedule for video, events, reports and backup copies.", "Supports governance and reduces uncontrolled archive growth."],
        ["Cyber resilience", "TLS in transit, encrypted secrets, patching, dependency review, backup and incident response runbook.", "Protects a public-sector operational platform."],
    ], [1.55, 3.7, 2.15])
    para(doc, "Vehicle registration information should be handled as controlled evidence. The system may preserve a detected crop and confidence for an authorised case, but it must not publish plate information in a public map, declare an offender or automate enforcement.")
    page_break(doc)

    # 17 cost architecture
    heading(doc, "16 Cost Architecture and High Cost Mitigation")
    para(doc, "The main expense risk in fleet video AI is not only the model. It is the combination of cameras, edge devices, data transfer, video storage, field installation, support and false-alert handling. MovIqSense addresses cost at the architecture level rather than adding cloud capacity after the fact.")
    table(doc, ["Cost pressure", "Uncontrolled approach", "MovIqSense mitigation"], [
        ["Camera hardware", "Replace every camera before proving the use case.", "Audit and reuse compatible road-facing cameras first."],
        ["Edge compute", "Deploy high-end GPU hardware on every bus from day one.", "Begin CPU or entry edge compute for one stream; scale only after load tests."],
        ["Mobile data", "Upload continuous HD video to the cloud.", "Run local inference; send compact event JSON and selected clips; use depot Wi-Fi sync."],
        ["Storage", "Keep all footage indefinitely in one hot store.", "Tier evidence by severity, configure retention and move non-active data to lower-cost storage."],
        ["Operations", "Treat every detected box as a field task.", "Use temporal confirmation, map clustering and human review before dispatch."],
        ["Integration", "Build one-off vendor interfaces for every agency.", "Use documented REST APIs, exportable records and an adapter approach."],
    ], [1.45, 2.75, 3.2])
    lead(doc, "Cost decision.", "The pilot should prove useful alerts per rupee, not maximum model count. A reliable front-camera workflow on ten buses is a stronger base than an expensive multi-camera deployment with no maintenance owner.")
    page_break(doc)

    # 18 budget
    heading(doc, "17 Illustrative Ten Bus Pilot Budget")
    para(doc, "The following is a budgetary planning view, not a vendor quotation. It assumes a six-month, ten-bus controlled pilot, reuse of compatible cameras and GPS where possible, and a small shared backend. Amounts exclude GST and require formal quotations, vehicle survey and procurement validation.")
    table(doc, ["Cost head", "Approximate planning value", "Planning note"], [
        ["Edge compute and vehicle installation", "Rs 7.50 lakh", "Rugged or semi-rugged compute, DC conversion, enclosure, mounting, wiring and commissioning; varies strongly by hardware choice."],
        ["Camera/GPS gap closure", "Rs 1.75 lakh", "Only for buses lacking usable front camera or authorised location feed."],
        ["Cloud, storage and connectivity for six months", "Rs 1.20 lakh", "Event-first design with capped evidence retention; higher if continuous upload is chosen."],
        ["Platform hardening and integrations", "Rs 6.00 lakh", "API, database, dashboard, audit logging, model registry and acceptance test work."],
        ["Field validation, training and support", "Rs 3.50 lakh", "Route survey, annotation, officer review sessions, defect verification and helpdesk."],
        ["Contingency at roughly 10 percent", "Rs 1.99 lakh", "Hardware variation, vehicle access delays, consumables and integration change."],
        ["Indicative pilot total", "Rs 21.94 lakh", "A realistic planning envelope before tax and formal procurement."],
    ], [2.35, 1.65, 3.4])
    para(doc, "A lower-cost proof of concept can start with two or three buses, existing cameras and a controlled uploaded-video workflow. The ten-bus pilot is proposed because it gives enough route repetition to evaluate clustering, operations and user adoption.")
    page_break(doc)

    # 19 timeline
    heading(doc, "18 Hackathon Delivery Plan and Post Hackathon Milestones")
    para(doc, "The SIH build should demonstrate a coherent vertical slice, not a citywide deployment. The immediate goal is a working chain that a judge can test: bus selection, camera or video input, detection, location, GIS display, workflow table, evidence and report generation.")
    table(doc, ["Phase", "Timing", "Deliverable"], [
        ["Hackathon build", "0 to 36 hours", "Driver dashboard, government dashboard, registered bus records, core detection pipeline, GIS events and a reviewable demo scenario."],
        ["Stabilisation", "Weeks 1 to 4", "Model registry cleanup, event schema, access controls, test videos, error handling and repeatable deployment guide."],
        ["Technical proof of concept", "Months 1 to 3", "Two to three buses, one corridor, camera/GPS audit, local evaluation set and weekly review."],
        ["Operational pilot", "Months 3 to 9", "Ten buses, two corridors, defect workflow, traffic analytics, measurable acceptance criteria and authority feedback."],
        ["Scale readiness", "Months 9 to 18", "Production database, monitoring, security testing, integration adapter, procurement pack and model retraining plan."],
        ["Early commercial expansion", "Months 18 to 36", "Two authority deployments of about 100 buses each if the pilot meets acceptance criteria."],
    ], [1.55, 1.3, 4.55])
    lead(doc, "Engineering discipline.", "Each phase has a stop-or-scale gate. A weak detection class is retrained or held for review rather than being promoted to an automated alert merely to increase the feature list.")
    page_break(doc)

    # 20 reliability
    heading(doc, "19 Reliability Monitoring and Operational Support")
    para(doc, "A city platform is judged on availability and trust, not only visual detection. The production design should therefore monitor camera heartbeat, GPS freshness, model load status, inference latency, queue depth, API success, storage capacity and dashboard errors. The aim is to tell an operator whether a missing observation is a quiet road or a broken device.")
    table(doc, ["Metric", "Example indicator", "Operational action"], [
        ["Camera health", "Last frame received and decode error count.", "Flag bus for depot check if stream is stale."],
        ["Location health", "Last GPS timestamp and coordinate validity.", "Mark event location uncertain; do not create precision work order."],
        ["Inference health", "FPS, latency, CPU/GPU state, failed-model count.", "Reduce stream load, restart service or schedule hardware review."],
        ["Event quality", "Duplicate rate, manual rejection rate and confidence distribution.", "Tune thresholds, model version or verification rule."],
        ["Platform health", "API availability, database backup status and evidence-store capacity.", "Escalate through runbook before operational information is lost."],
    ], [1.45, 3.25, 2.7])
    para(doc, "A simple service-level plan for a pilot can define observation availability, response time for a failed edge device, data recovery procedure and authority escalation contacts. These are more useful than promising unrealistic 100 percent availability.")
    page_break(doc)

    # 21 impact metrics
    heading(doc, "20 Impact Measurement Framework")
    para(doc, "Impact must be measured against a baseline established with the pilot authority. The project should not state that it has reduced accidents or repair time until that result has been independently observed. The following metrics make the value proposition testable.")
    table(doc, ["Outcome", "Baseline and target method", "Evidence source"], [
        ["Defect discovery time", "Compare time from first visible event to registered case with current complaint or inspection route.", "System event log and department case register."],
        ["Inspection efficiency", "Measure verified defects per field inspection trip and duplicate-event reduction.", "Maintenance team confirmation records."],
        ["Incident response awareness", "Measure alert-to-dashboard and dashboard-to-review time for high-severity simulated or authorised events.", "Audit log and control-room record."],
        ["Traffic insight coverage", "Count route-time observations and locations not covered by existing fixed CCTV.", "Fleet route map and camera coverage inventory."],
        ["Data-cost reduction", "Compare event-first transmission volume with continuous HD video alternative.", "Network usage and storage reports."],
        ["User adoption", "Track active operational users, review completion and useful-alert rating.", "Role audit and periodic feedback form."],
    ], [1.65, 3.55, 2.2])
    lead(doc, "Suggested pilot objective.", "Aim to demonstrate that a verified observation can be produced and placed in the correct authority queue faster than a manual-only route, while keeping staff review workload acceptable.")
    page_break(doc)

    # 22 TAM alignment
    heading(doc, "21 Market and Procurement Alignment")
    para(doc, "MovIqSense is best positioned as Government B2G software plus field integration. The purchaser is not an individual driver. It is likely to be a State Transport Undertaking, municipal corporation, Smart City ICCC, road-maintenance agency or a consortium led by a public-sector technology partner. The system can be procured as a pilot, a per-bus platform subscription, an authority analytics licence and optional integration services.")
    table(doc, ["Market layer", "Illustrative scope", "Planning value"], [
        ["TAM", "50,000 high-potential city and public fleet buses plus 70 authority licences.", "Rs 231 crore annual recurring revenue; internal planning assumption."],
        ["SAM", "10,000 PM eBus Sewa and comparable digitally ready buses plus 30 authority licences.", "Rs 48 crore annual recurring revenue; internal planning assumption."],
        ["SIM", "Two early adopter authorities and 200 buses over 36 months.", "Rs 1.14 crore recurring revenue; approximately Rs 1.54 crore first-year contract value including implementation."],
    ], [1.1, 3.55, 2.75])
    para(doc, "These figures are not tender prices or market guarantees. They are a bottom-up planning model based on Rs 42,000 per bus per year, authority licences and separate implementation fees. A real opportunity must pass a fleet audit, procurement process, technical evaluation and pilot acceptance stage.")
    page_break(doc)

    # 23 risk
    heading(doc, "22 Risk Register and Mitigation Plan")
    table(doc, ["Risk", "Potential effect", "Mitigation and owner"], [
        ["Model false positives in rain, glare or shadows", "Wasted inspection effort and lower user trust.", "Local test set, temporal confirmation, threshold calibration and human review; ML lead."],
        ["Camera or GPS incompatibility", "Delay in onboarding fleet buses.", "Pre-installation survey, camera/AVL adapter checklist and staged bus selection; integration lead."],
        ["Poor connectivity", "Delayed evidence or dashboard update.", "Store-and-forward queue, event-first transport and depot Wi-Fi sync; edge lead."],
        ["Sensitive evidence exposure", "Privacy and legal risk.", "Role-based access, audit log, encryption, retention policy and authorised review; security owner."],
        ["No maintenance owner for defects", "Good detections do not become repairs.", "Agree workflow, status ownership and escalation SLA before pilot; authority sponsor."],
        ["Procurement delay", "Prototype cannot convert to field adoption quickly.", "Use fixed-scope PoC, published acceptance metrics and open API documentation; project lead."],
    ], [1.6, 2.8, 3.0])
    para(doc, "The core mitigation is staged validation. MovIqSense should earn wider scope through corridor evidence and operational adoption rather than attempting to deploy every detector, camera and integration at once.")
    page_break(doc)

    # 24 closing + sources
    heading(doc, "23 Recommendation and Source Notes")
    para(doc, "MovIqSense is a practical Smart Automation proposal because it creates a reusable observation network from vehicles that already move through the city. It couples edge AI with a central GIS workflow, controls cost through event-first data transfer, and keeps high-consequence decisions with authorised public officials. The project is not presented as an infallible surveillance or enforcement tool. It is a decision-support platform designed to improve the speed, coverage and traceability of urban road intelligence.")
    para(doc, "For SIH evaluation, the strongest proof is the operational chain: a road-facing video produces a bounded detection; the event receives a bus identity, timestamp and location; the government map shows it; a responsible user reviews it; and the observation becomes either a closed case, a field task or an evidence record. That workflow is both technically demonstrable and aligned with the stated problem.")
    heading(doc, "Primary public references", 2)
    compact_source(doc, "Ministry of Road Transport and Highways, Road Accidents in India 2023. Reported 4,80,583 road accidents, 1,72,890 deaths and 4,62,825 injuries. https://morth.nic.in/sites/default/files/Road-Accident-in-India-2023-Publications.pdf")
    compact_source(doc, "Ministry of Housing and Urban Affairs, PM eBus Sewa portal. Programme context: 10,000 e-buses on PPP model, ITMS and NCMC context, urban bus operations and support information. https://pm-ebus-sewa.mohua.gov.in/")
    compact_source(doc, "Press Information Bureau, Cabinet approval for PM eBus Sewa, 16 August 2023. 10,000 e-buses in 169 cities, estimated cost Rs 57,613 crore, central support Rs 20,000 crore. https://pm-ebus-sewa.mohua.gov.in/wp-content/uploads/2025/08/Press-Release_Press-Information-Bureau-1.pdf")
    compact_source(doc, "All model performance values, cost values, market estimates and deployment figures in this report are labelled planning assumptions unless an official source is named. They require vendor quotation, local evaluation, security review and authority approval before procurement.")

    doc.core_properties.title = "MovIqSense Complete SIH 2026 Technical Report"
    doc.core_properties.author = "MovIqSense SIH Team"
    doc.core_properties.subject = "Bharat Electronics Limited Smart Automation Problem Statement 26124"
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
