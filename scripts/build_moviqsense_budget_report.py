from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "docs" / "MovIqSense_SIH_2026_Budget_and_Implementation_Report.docx"
NAVY, BLUE, LIGHT, TEXT, BORDER, GREEN = "132238", "1F4E79", "F5F9FC", "1F2937", "D9E2F3", "0F6B4D"


def shade(cell, fill):
    props = cell._tc.get_or_add_tcPr()
    node = OxmlElement("w:shd")
    node.set(qn("w:fill"), fill)
    props.append(node)


def format_cell(cell):
    props = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        edge = OxmlElement("w:" + side)
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "6")
        edge.set(qn("w:color"), BORDER)
        borders.append(edge)
    props.append(borders)
    margin = OxmlElement("w:tcMar")
    for side in ("top", "start", "bottom", "end"):
        edge = OxmlElement("w:" + side)
        edge.set(qn("w:w"), "105")
        edge.set(qn("w:type"), "dxa")
        margin.append(edge)
    props.append(margin)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def run(p, value, bold=False, color=TEXT, size=10.0, italic=False):
    r = p.add_run(value)
    r.bold, r.italic = bold, italic
    r.font.name = "Aptos"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    return r


def paragraph(doc, value, size=10.0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.12
    run(p, value, size=size)
    return p


def bullet(doc, value):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.04
    run(p, value, size=9.8)
    return p


def heading(doc, value, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.space_before = Pt(10 if level == 1 else 6)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(value)
    r.bold = True
    r.font.name = "Aptos Display"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    r.font.size = Pt(14 if level == 1 else 11.5)
    r.font.color.rgb = RGBColor(0, 0, 0)
    return p


def table(doc, headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.autofit = False
    for i, label in enumerate(headers):
        c = t.rows[0].cells[i]
        c.width = Inches(widths[i])
        shade(c, NAVY)
        format_cell(c)
        p = c.paragraphs[0]
        run(p, label, True, "FFFFFF", 8.8)
    for row_i, values in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(values):
            c = cells[i]
            c.width = Inches(widths[i])
            shade(c, "FFFFFF" if row_i % 2 == 0 else LIGHT)
            format_cell(c)
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            run(p, value, size=8.65)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t


def page_break(doc):
    doc.add_page_break()


def cover(doc):
    for _ in range(6):
        doc.add_paragraph()
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("MovIqSense")
    r.font.name = "Aptos Display"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    r.font.size = Pt(34)
    r.bold = True
    r.font.color.rgb = RGBColor(0, 0, 0)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(p, "Pilot Budget and Implementation Planning Report", True, BLUE, 16)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(p, "AI Powered Mobile Urban Intelligence Platform Using Public Transport Fleet", False, TEXT, 12)
    for _ in range(5):
        doc.add_paragraph()
    table(doc, ["Submission Detail", "Value"], [
        ["Problem Statement", "SIH 2026 - PS 26124"],
        ["Organisation", "Bharat Electronics Limited"],
        ["Theme", "Smart Automation"],
        ["Category", "Software"],
        ["Prepared for", "Smart India Hackathon evaluation and pilot-planning discussion"],
        ["Budget basis", "10-bus, six-month city pilot; figures are approximate planning values and require vendor quotations before procurement"],
    ], [2.05, 5.5])
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(20)
    run(p, "Prepared by Team MetaMinds 2.0", True, NAVY, 11)


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin, sec.bottom_margin = Inches(0.62), Inches(0.62)
    sec.left_margin, sec.right_margin = Inches(0.68), Inches(0.68)
    doc.styles["Normal"].font.name = "Aptos"
    doc.styles["Normal"].font.size = Pt(10)
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(fp, "MovIqSense | SIH 2026 | Budgetary planning document | Not a commercial quotation", False, "667085", 8.1)

    cover(doc)
    page_break(doc)

    heading(doc, "1 Executive Recommendation")
    paragraph(doc, "If we were presenting MovIqSense to a Smart India Hackathon judge, we would not ask the government to buy an expensive citywide system on day one. We would request a controlled six-month pilot on ten buses across two high-use corridors. The pilot would prove that existing bus cameras, GPS and compact edge processing can create timely, useful road-safety and civic-maintenance intelligence.")
    paragraph(doc, "Our recommended pilot envelope is ₹24 lakh, including a 10% contingency reserve. The amount is deliberately higher than a simple software demo because it includes the real-world items that decide whether a field pilot works: ruggedised edge computing, vehicle installation, power protection, 4G connectivity, secure storage, staff training, testing, and operational support. If the transport authority already has compatible cameras and GPS/AVL, the pilot avoids major camera and tracker purchases.")
    table(doc, ["Budget View", "Amount", "Meaning"], [
        ["Core implementation and field deployment", "₹16.81 lakh", "Hardware, software engineering, integration, cloud, validation, training and support."],
        ["Contingency reserve (10%)", "₹2.18 lakh", "Covers price movement, connector changes, installation rework and unforeseen field requirements."],
        ["Recommended six-month pilot budget", "₹23.99 lakh", "Rounded planning envelope: ₹24 lakh."],
        ["Approximate cost per connected bus", "₹2.40 lakh", "Includes shared central platform and one-time pilot activities; it reduces at fleet scale."],
    ], [2.45, 1.25, 3.85])
    paragraph(doc, "This is a budgetary estimate, not a tender price. Final amounts should be based on three vendor quotations, GeM availability, tax treatment, actual camera interfaces, local installation conditions and whether the authority provides GPS, SIMs, cloud tenancy or server space.")
    heading(doc, "Why the pilot is worth funding", 2)
    for item in [
        "It reuses a city asset that is already moving every day: public buses and their cameras.",
        "It turns raw video into geo-tagged events that road, traffic and transport teams can act upon.",
        "It tests a low-bandwidth model: metadata and evidence clips are sent instead of continuous video.",
        "It creates measurable evidence for a later procurement decision instead of requesting a large unvalidated rollout.",
    ]:
        bullet(doc, item)
    page_break(doc)

    heading(doc, "2 Planning Basis and Scope")
    paragraph(doc, "The budget is built around a modest but credible city pilot. Ten buses are sufficient to compare routes, test different lighting and weather conditions, observe repeated road defects, and demonstrate multi-bus verification. The pilot should run for six months because a shorter demonstration may not capture rainfall, peak traffic variation, maintenance response and repeat hazard observations.")
    table(doc, ["Parameter", "Planning Assumption", "Reason for Inclusion"], [
        ["Fleet", "10 buses", "Enough vehicles to prove cooperative verification without a high upfront commitment."],
        ["Pilot duration", "6 months", "Allows onboarding, calibration, field use, review and a closure assessment."],
        ["Camera arrangement", "Existing front-facing camera preferred; up to three streams evaluated in phase two", "Avoids unnecessary hardware spend during the first pilot."],
        ["Connectivity", "4G, 5-10 GB per bus per month under event-based upload", "Events and evidence clips cost far less than continuous video upload."],
        ["Central users", "10-20 authorised dashboard users", "Transport, PWD, traffic police and pilot coordinators."],
        ["Road observations", "Potholes, waterlogging, traffic density, pedestrians, accidents and selected infrastructure cues", "Directly maps to PS 26124 and supports a measurable initial scope."],
    ], [1.4, 2.65, 3.5])
    heading(doc, "What is intentionally outside the first pilot", 2)
    paragraph(doc, "We would not budget for a new camera network across every bus, a citywide private cloud, automatic e-challan integration or unsupervised number-plate enforcement. These are later-stage decisions. In the pilot, plate output remains evidence for authorised human verification. Keeping this boundary is important: it protects the project from overclaiming and keeps resources focused on a working end-to-end workflow.")
    heading(doc, "Government relevance", 2)
    paragraph(doc, "The PM-eBus Sewa programme provides a strong policy signal for connected, technology-enabled public transport. Government materials describe a 10,000 e-bus programme and Intelligent Transit Management System context. MovIqSense does not replace a fleet-management system; it adds a road-condition, safety and civic-intelligence layer to the transport ecosystem.")
    page_break(doc)

    heading(doc, "3 Deployment Architecture and Cost Logic")
    paragraph(doc, "The budget follows one rule: compute near the vehicle, send only what is useful, and retain a verifiable trail for government action. This is more affordable than sending every camera stream to the cloud. A compact edge computer samples frames, runs selected models, records GPS-linked events and uploads structured JSON telemetry plus selected evidence frames or short clips.")
    table(doc, ["Layer", "Pilot Design", "Cost Impact"], [
        ["Vehicle layer", "Existing camera, 4G/GPS input, edge AI unit, power protection and mounting.", "One-time per-bus cost; avoid replacement of usable camera and GPS hardware."],
        ["Communications", "Event-driven upload, local buffering during weak network, delayed synchronisation.", "Controls monthly data and cloud egress cost."],
        ["Central platform", "FastAPI services, model registry, dashboard, GIS map, database, evidence store and alerts.", "Shared platform cost decreases per bus as fleet size grows."],
        ["Authority workflow", "Defect status, repair deadline, incident evidence, audit trail and priority queue.", "Makes the pilot operationally useful rather than a visual demonstration only."],
    ], [1.25, 3.45, 2.85])
    heading(doc, "Costing principles", 2)
    for item in [
        "Use existing bus CCTV and AIS-140/GPS equipment where technically compatible.",
        "Use one edge unit per bus only for road-facing streams during the pilot; add rear and side streams after performance validation.",
        "Use open-source software components where appropriate, but budget for engineering, testing, security and support rather than treating software as free.",
        "Separate one-time capital expense from recurring operating expense, so government reviewers can compare scale-up options fairly.",
        "Include contingency because automotive connectors, mounting, electrical isolation and field installation commonly create small but real cost variation.",
    ]:
        bullet(doc, item)
    page_break(doc)

    heading(doc, "4 Pilot Bill of Materials - Per Bus")
    paragraph(doc, "The following estimates assume that a working front camera and basic GPS are already available on each bus. Edge hardware is budgeted at a conservative Indian market range because availability and exchange-rate movement affect developer-kit and industrial-compute pricing. Formal procurement should request ruggedised equivalents, warranty terms and automotive power compatibility.")
    table(doc, ["Per Bus Item", "Quantity", "Budgetary Unit Cost", "10 Bus Total", "Planning Note"], [
        ["Edge AI compute unit with enclosure", "1", "₹52,000", "₹5,20,000", "Jetson Orin Nano-class or equivalent; includes basic thermal enclosure."],
        ["NVMe storage, 512 GB", "1", "₹4,500", "₹45,000", "Local event buffer and model storage; not full-time raw-video archive."],
        ["4G industrial router / modem", "1", "₹12,000", "₹1,20,000", "Dual-SIM-capable budget assumption; final choice depends on authority network policy."],
        ["AIS-140 GPS fallback device", "1", "₹4,500", "₹45,000", "Only used if the existing AVL feed cannot be consumed; can be removed where GPS is available."],
        ["Vehicle power converter, fuse, cable and protection", "1", "₹6,000", "₹60,000", "Required for safe DC integration and voltage fluctuation protection."],
        ["Mounting bracket, enclosure fitting and connectors", "1", "₹5,500", "₹55,000", "Rugged mounting and camera-interface adaptation."],
        ["Installation and commissioning labour", "1", "₹8,000", "₹80,000", "Includes vehicle inspection, fitting, testing and handover."],
        ["Per-bus hardware and installation subtotal", "", "₹92,500", "₹9,25,000", "Assumes existing camera reuse."],
    ], [1.85, 0.55, 1.3, 1.15, 2.0])
    heading(doc, "Hardware alternatives", 2)
    table(doc, ["Alternative", "Effect on Budget", "When to Select It"], [
        ["Software-first pilot using a laptop or depot device", "Reduces per-bus edge hardware but weakens onboard proof.", "Best for SIH demonstration and pre-pilot validation."],
        ["Use existing AVL/GPS API", "Saves roughly ₹45,000 for ten fallback trackers.", "When the STU can provide live location through an authorised API."],
        ["Use authority-provided SIMs", "Removes recurring M2M data line item.", "When enterprise telecom procurement is already available."],
        ["Add side and rear cameras later", "Avoids premature three-stream hardware sizing.", "After front-camera accuracy and installer workflow are proven."],
    ], [2.0, 2.65, 2.2])
    page_break(doc)

    heading(doc, "5 Software Engineering and Integration Budget")
    paragraph(doc, "A credible government pilot needs more than a trained model. The work includes model packaging, API reliability, event storage, the GIS dashboard, user access, testing, alert logic, evidence reporting and documentation. This table values student-team and professional support effort transparently so the deployment estimate does not hide the real engineering work.")
    table(doc, ["Work Package", "Estimated Effort", "Budget", "Deliverable"], [
        ["Edge AI and model optimisation", "180 hours", "₹1,80,000", "Model loading, inference optimisation, confidence logic, temporal verification and road-condition test suite."],
        ["Backend and data services", "160 hours", "₹1,60,000", "FastAPI endpoints, event schema, bus records, evidence management, database and APIs."],
        ["Government GIS dashboard", "140 hours", "₹1,40,000", "Live map, defect table, priority queue, traffic analysis and officer workflow."],
        ["Driver interface and field UX", "80 hours", "₹80,000", "Camera/upload flow, GPS state, live overlay, retry states and basic accessibility."],
        ["Integration and testing", "100 hours", "₹1,00,000", "Camera input, GPS/AVL feed, event telemetry, installation acceptance and field checks."],
        ["Security and documentation", "60 hours", "₹60,000", "Role matrix, audit approach, data retention plan, test plan and operator guide."],
        ["Software and integration subtotal", "720 hours", "₹7,20,000", "One-time pilot implementation cost."],
    ], [2.1, 1.15, 1.1, 3.05])
    heading(doc, "Why open source does not mean zero cost", 2)
    paragraph(doc, "MovIqSense can use open-source libraries such as Python, FastAPI, OpenCV, YOLO-compatible tooling, Leaflet and OpenStreetMap. This avoids licence-heavy software acquisition. However, government deployment still requires engineering time, testing, security controls, data governance, model evaluation and support. The budget therefore charges for the work that makes open technology safe and usable in the field, not for unnecessary licence fees.")
    page_break(doc)

    heading(doc, "6 Cloud Data Security and Six Month Operations")
    paragraph(doc, "The pilot should run on a small secure cloud tenancy or an authority-approved server. The cost is kept modest by uploading event metadata and selected evidence rather than continuous high-definition video. Local buffering allows the bus to continue operating during temporary network loss and synchronise later.")
    table(doc, ["Recurring Cost Item", "Monthly Estimate", "6 Month Budget", "Control Measure"], [
        ["Cloud compute, API and database", "₹18,000", "₹1,08,000", "Small instance sizing; scale only after measured demand."],
        ["Object storage and backup", "₹7,000", "₹42,000", "Store selected evidence; retention limits for raw uploads."],
        ["M2M data connectivity", "₹1,200 per bus", "₹72,000", "10 buses; event-based upload and Wi-Fi sync at depot where possible."],
        ["Monitoring, alerts and logs", "₹5,000", "₹30,000", "Tracks uptime, failures and access history."],
        ["Field support and corrective visits", "₹20,000", "₹1,20,000", "Reserved for connector, mount and configuration issues."],
        ["Training and review workshops", "₹20,000", "₹1,20,000", "Driver briefing and authority review sessions."],
        ["Six-month operations subtotal", "", "₹4,92,000", "Supports the pilot after deployment."],
    ], [2.1, 1.35, 1.25, 2.7])
    heading(doc, "Data protection and evidence controls", 2)
    for item in [
        "Use HTTPS/TLS for data in transit and authenticated API access for authorised users.",
        "Store the minimum information needed for the event; avoid permanent upload of routine video.",
        "Use role-based access for fleet operator, maintenance officer, traffic authority and administrator functions.",
        "Treat plate crops as controlled evidence and require human verification before any enforcement workflow.",
        "Maintain audit logs, retention settings and a documented procedure for deletion or archival.",
    ]:
        bullet(doc, item)
    page_break(doc)

    heading(doc, "7 Consolidated Six Month Pilot Budget")
    paragraph(doc, "The consolidated figure below is the budget we would present to a judge or pilot partner. It is intentionally itemised. This makes it easier for an authority to reduce or increase scope without losing visibility into the assumptions.")
    table(doc, ["Budget Head", "Amount", "Share of Core Budget", "Comment"], [
        ["Per-bus hardware and commissioning", "₹9,25,000", "55.0%", "Ten edge-enabled buses using existing cameras where possible."],
        ["Software engineering and integration", "₹7,20,000", "42.8%", "One-time platform, AI, dashboard, API, test and documentation work."],
        ["Six-month cloud, connectivity, support and training", "₹4,92,000", "29.3%", "Recurring operations; overlaps are funded by shared pilot resources."],
        ["Pilot management, data labelling and validation reserve", "₹44,000", "2.6%", "Field review, sample audits and acceptance reporting."],
        ["Core budget before contingency", "₹16,81,000", "100.0%", "Operational planning baseline."],
        ["Contingency reserve at 10%", "₹2,18,100", "", "Protects the pilot from hardware price movement and field changes."],
        ["Recommended pilot approval amount", "₹23,99,100", "", "Rounded to ₹24 lakh."],
    ], [2.2, 1.25, 1.35, 2.6])
    heading(doc, "Important note on category overlap", 2)
    paragraph(doc, "The percentage column is provided only as a view of the core budget components; some programme-management and operational inputs are shared across hardware and software work. The final total is calculated from the budgeted rupee values, not by adding percentages. This prevents misleading financial presentation.")
    heading(doc, "What success should look like at the end of six months", 2)
    table(doc, ["Metric", "Pilot Measurement"], [
        ["Technical reliability", "Percentage of scheduled buses successfully transmitting health status and events."],
        ["Alert usefulness", "Proportion of sampled alerts accepted, rejected or merged by authorised officers."],
        ["Response improvement", "Time from verified event to authority acknowledgement and action assignment."],
        ["Maintenance intelligence", "Number of geo-tagged defects confirmed, deduplicated and closed."],
        ["Traffic value", "Number of recurring congestion zones and route observations visible to operations teams."],
    ], [2.0, 5.4])
    page_break(doc)

    heading(doc, "8 How MovIqSense Controls Cost")
    paragraph(doc, "The largest risk in projects like this is treating every bus as a high-bandwidth surveillance unit. MovIqSense avoids that. The design treats a bus as an intelligent sensor: process locally, upload only meaningful events, and use multiple buses to verify the same location before generating repeated maintenance work.")
    table(doc, ["High Cost Risk", "MovIqSense Response", "Expected Benefit"], [
        ["Continuous cloud video upload", "Event-only JSON telemetry and selected geo-clips; depot Wi-Fi sync where available.", "Avoids recurring high data and storage bills."],
        ["Replacing all camera systems", "Reuse compatible front cameras and add interfaces only where needed.", "Cuts initial capital expenditure."],
        ["Over-sized AI hardware", "Start with one road-facing stream and validate workload before adding more streams.", "Matches compute spend to actual pilot use."],
        ["Duplicate pothole or waterlogging reports", "Cluster repeated frame and multi-bus observations by location and time.", "Reduces duplicate work orders and officer review time."],
        ["Manual review of every video", "Use confidence thresholds, temporal verification and evidence snapshots.", "Focuses human attention on actionable cases."],
        ["Vendor lock-in", "Use API-first design and interoperable data formats; preserve data ownership with the authority.", "Improves procurement flexibility and long-term value."],
    ], [1.75, 3.25, 2.4])
    heading(doc, "Savings scenario")
    paragraph(doc, "A ten-bus pilot is not expected to replace road inspectors. Its immediate value is to make inspectors more targeted. Instead of sending teams to inspect roads only after complaints arrive, officers receive a prioritised map with confidence, route context and visual evidence. If a city already has bus cameras and GPS, avoiding new camera procurement is the most important early saving. At larger fleet sizes, the shared dashboard, model registry and evidence system are spread across more buses, reducing average cost per bus.")
    page_break(doc)

    heading(doc, "9 Phased Funding Plan")
    paragraph(doc, "A staged plan makes the proposal easier to approve. Each stage has a clear decision point. The next expenditure is released only after the previous stage proves technical and operational value.")
    table(doc, ["Stage", "Duration", "Indicative Budget", "Decision Gate"], [
        ["Stage 0 - SIH prototype", "0-2 months", "₹1.5-2.5 lakh equivalent in student, cloud and demonstration support", "Prove video input, detection, GPS, GIS event and government workflow."],
        ["Stage 1 - controlled technical pilot", "2-3 months", "₹5-7 lakh", "Validate camera compatibility, edge hardware, alert latency and operator usability on 2-3 buses."],
        ["Stage 2 - operational pilot", "6 months", "₹24 lakh total for 10 buses", "Measure verified events, field reliability, response time and maintenance adoption."],
        ["Stage 3 - city expansion", "12 months", "To be tendered after pilot; target 50-100 buses", "Scale only when accuracy, support model and integration requirements are evidenced."],
    ], [1.55, 1.0, 2.3, 2.55])
    heading(doc, "Possible funding routes", 2)
    for item in [
        "BEL-supported innovation or proof-of-concept partnership.",
        "State Transport Undertaking and Smart City pilot funding.",
        "Corporate social responsibility support for school-zone and road-safety use cases.",
        "Technology partner sponsorship for edge hardware, cloud credits or connectivity.",
        "PPP or managed-service procurement after successful pilot evaluation.",
    ]:
        bullet(doc, item)
    page_break(doc)

    heading(doc, "10 Procurement Governance and Risk Management")
    paragraph(doc, "A strong SIH proposal should acknowledge that government technology is judged not only by features but also by reliability, procurement readiness, safety and accountability. The pilot should use an approval process that is simple enough to execute but disciplined enough to create evidence for future scale-up.")
    table(doc, ["Risk", "Likely Issue", "Mitigation and Budget Response"], [
        ["Model false positives", "Rain, shadows, poor light and road texture can create incorrect detections.", "Use confidence threshold, multi-frame confirmation, multi-bus verification and officer review; include validation budget."],
        ["Hardware price fluctuation", "Edge device and storage prices change with availability and exchange rates.", "Use 10% contingency; obtain three quotations or GeM comparison before purchase."],
        ["Vehicle integration delay", "Camera connector or power interfaces vary across buses.", "Complete a 2-3 bus technical assessment before purchasing all ten installation kits."],
        ["Network gaps", "Live upload may fail on some corridors.", "Local buffering and delayed sync; event-only transmission limits data dependency."],
        ["Privacy concern", "Video and plate data require controlled use.", "Role-based access, evidence retention policy, audit logs and human verification."],
        ["Low officer adoption", "Dashboard may not fit existing workflow.", "Co-design alert categories with transport, PWD and police representatives; provide training."],
    ], [1.45, 2.55, 3.4])
    heading(doc, "Recommended procurement method", 2)
    paragraph(doc, "For a small pilot, we recommend an outcome-based proof-of-concept procurement or innovation challenge with a defined 10-bus scope, measurable acceptance criteria and phased payment. The authority should own the operational data. Vendors or student teams should provide open API documentation, installation records, asset serial numbers, support contacts and a clear exit or data-export plan.")
    page_break(doc)

    heading(doc, "11 Scale Up Economics and Sustainability")
    paragraph(doc, "The pilot price per bus is intentionally higher than the expected city-scale price because the first deployment pays for platform setup, integration, test effort and field learning. Once the dashboard, data model and operating procedures are stable, these shared costs are distributed across a larger fleet.")
    table(doc, ["Deployment Size", "Indicative One Time Cost Per Bus", "Indicative Annual Platform Cost Per Bus", "Reason"], [
        ["10-bus pilot", "₹0.93 lakh hardware plus shared setup", "Higher due to small scale", "Includes learning, installation validation and central platform setup."],
        ["50-bus city rollout", "Expected to reduce through bulk purchase", "₹45,000-₹60,000", "Shared dashboard and support spread across more vehicles."],
        ["100+ bus deployment", "Subject to tender and hardware mix", "₹35,000-₹50,000", "Volume pricing, shared support and authority-provided infrastructure can reduce cost."],
    ], [1.35, 2.1, 2.05, 2.0])
    paragraph(doc, "These scale-up figures are directional targets, not quotations. They show why a measured pilot is financially sensible: it creates real evidence about device reliability, data consumption, alert value and field support before a city commits to a larger contract.")
    heading(doc, "Long term value")
    for item in [
        "Road defects can be detected earlier and ranked with route, traffic and evidence context.",
        "Transport, traffic and maintenance departments can work from the same geo-tagged event record.",
        "Daily bus movement creates broader observation coverage without deploying a completely new fixed-camera network.",
        "Authorities receive evidence for maintenance planning, recurring hotspot analysis and more focused inspection.",
        "The system can extend from city buses to municipal vehicles, school buses, waste-collection vehicles and emergency fleets where policy permits.",
    ]:
        bullet(doc, item)
    page_break(doc)

    heading(doc, "12 Conclusion and Ask")
    paragraph(doc, "MovIqSense is not proposed as a costly surveillance project. It is proposed as a practical government decision-support system that makes better use of infrastructure already on the road. The first investment is a ten-bus, six-month pilot with a recommended planning envelope of ₹24 lakh. That pilot should answer four questions with real evidence: Can the system detect useful hazards? Can it reduce response time? Can officers use the dashboard? Can the cost fall when the fleet grows?")
    paragraph(doc, "Our ask is not for blind scale-up. Our ask is for a controlled pilot, shared evaluation criteria and an opportunity to prove that bus cameras can become a trusted source of urban intelligence. If the pilot succeeds, the authority will have a clear procurement baseline, verified cost data, trained users and a scalable path to a safer, more responsive city.")
    heading(doc, "Sources and budget notes")
    sources = [
        "PM-eBus Sewa, Ministry of Housing and Urban Affairs: 10,000 e-bus programme and Intelligent Transit Management System context. https://pm-ebus-sewa.mohua.gov.in/",
        "Prime Minister of India, Cabinet approval for PM-eBus Sewa: 10,000 e-buses in 169 cities; total scheme cost ₹57,613 crore. https://www.pmindia.gov.in/en/news_updates/cabinet-approves-pm-ebus-sewa-for-augmenting-city-bus-operations-priority-to-cities-having-no-organized-bus-service/",
        "Indicative Indian market references used only to set budget ranges: industrial 4G router listings and AIS-140 tracker price guides. Exact models, taxes, warranty and lead time require formal vendor quotation.",
        "All costs are approximate planning values in Indian rupees for SIH evaluation. They exclude any statutory taxes that may apply under the final procurement route unless a supplier quotation expressly includes them.",
    ]
    for source in sources:
        bullet(doc, source)

    doc.core_properties.title = "MovIqSense SIH 2026 Budget and Implementation Report"
    doc.core_properties.author = "MetaMinds 2.0"
    doc.core_properties.subject = "SIH 2026 Problem Statement 26124"
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
