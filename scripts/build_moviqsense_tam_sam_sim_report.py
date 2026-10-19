from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "docs" / "MovIqSense_TAM_SAM_SIM_Market_Opportunity_Report.docx"
NAVY, BLUE, LIGHT, TEXT, BORDER = "132238", "1F4E79", "F5F9FC", "1F2937", "D9E2F3"


def add_run(p, value, bold=False, color=TEXT, size=10.3):
    r = p.add_run(value)
    r.bold = bold
    r.font.name = "Aptos"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    return r


def fill(cell, color):
    props = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    props.append(shd)
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        node = OxmlElement("w:" + side)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "6")
        node.set(qn("w:color"), BORDER)
        borders.append(node)
    props.append(borders)
    mar = OxmlElement("w:tcMar")
    for side in ("top", "start", "bottom", "end"):
        node = OxmlElement("w:" + side)
        node.set(qn("w:w"), "110")
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    props.append(mar)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def p(doc, value, size=10.3):
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.line_spacing = 1.14
    add_run(para, value, size=size)
    return para


def bullet(doc, value):
    para = doc.add_paragraph(style="List Bullet")
    para.paragraph_format.space_after = Pt(3)
    para.paragraph_format.line_spacing = 1.04
    add_run(para, value, size=9.9)
    return para


def h(doc, value, level=1):
    para = doc.add_paragraph(style=f"Heading {level}")
    para.paragraph_format.space_before = Pt(10 if level == 1 else 6)
    para.paragraph_format.space_after = Pt(4)
    r = para.add_run(value)
    r.bold = True
    r.font.name = "Aptos Display"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    r.font.size = Pt(14 if level == 1 else 11.6)
    r.font.color.rgb = RGBColor(0, 0, 0)
    return para


def tbl(doc, headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    t.style = "Table Grid"
    for i, header in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.width = Inches(widths[i])
        fill(cell, NAVY)
        add_run(cell.paragraphs[0], header, bold=True, color="FFFFFF", size=8.9)
    for ri, values in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(values):
            cell = cells[i]
            cell.width = Inches(widths[i])
            fill(cell, "FFFFFF" if ri % 2 == 0 else LIGHT)
            cell.paragraphs[0].paragraph_format.space_after = Pt(0)
            add_run(cell.paragraphs[0], value, size=8.75)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t


def br(doc):
    doc.add_page_break()


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    s = doc.sections[0]
    s.top_margin, s.bottom_margin = Inches(0.62), Inches(0.62)
    s.left_margin, s.right_margin = Inches(0.7), Inches(0.7)
    doc.styles["Normal"].font.name = "Aptos"
    doc.styles["Normal"].font.size = Pt(10.3)
    footer = s.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(footer, "MovIqSense | SIH 2026 | PS 26124 | Market opportunity planning report", color="667085", size=8.1)

    # Page 1
    for _ in range(6):
        doc.add_paragraph()
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("MovIqSense")
    r.bold = True
    r.font.name = "Aptos Display"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    r.font.size = Pt(34)
    r.font.color.rgb = RGBColor(0, 0, 0)
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(sub, "TAM SAM SIM Market Opportunity Report", bold=True, color=BLUE, size=17)
    sub2 = doc.add_paragraph()
    sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(sub2, "AI Powered Mobile Urban Intelligence Platform Using Public Transport Fleet", size=12)
    for _ in range(5):
        doc.add_paragraph()
    tbl(doc, ["Submission Detail", "Value"], [
        ["Problem Statement", "SIH 2026 - Problem Statement 26124"],
        ["Organisation", "Bharat Electronics Limited"],
        ["Theme and Category", "Smart Automation | Software"],
        ["Requested Market Terms", "TAM, SAM and SIM"],
        ["SIM definition in this report", "Serviceable Immediately Obtainable Market; equivalent to the first achievable segment often called SOM."],
        ["Report position", "Budgetary, assumption-led planning document for SIH evaluation; not a sales forecast or tender quotation."],
    ], [2.15, 5.45])
    br(doc)

    # Page 2
    h(doc, "1 Executive Summary")
    p(doc, "MovIqSense is a government technology platform that converts public buses into mobile sensing units. It analyses bus-camera video and GPS information to identify road defects, waterlogging, traffic density, unsafe pedestrian situations, accidents and selected evidence for authorised review. The central GIS dashboard converts those observations into a repair, traffic-management and incident-response workflow.")
    p(doc, "Our market thesis is straightforward: buses already travel daily through the roads that need observation. The first commercial opportunity is not every vehicle in India. It is the smaller, more practical group of city bus fleets that already have cameras, GPS, digital fleet operations or Smart City command-centre connections. This report therefore avoids inflated market claims and uses a bottom-up model that begins with a 10,000 e-bus public-programme reference point.")
    tbl(doc, ["Market Layer", "Scope Used in This Report", "Annual Recurring Revenue Estimate"], [
        ["TAM", "50,000 high-potential urban and public-fleet bus units in a long-term adoption universe.", "₹231 crore"],
        ["SAM", "10,000 PM-eBus Sewa and comparable high-readiness city e-bus units.", "₹48 crore"],
        ["SIM", "200 buses across two early-adopter city pilots within 36 months.", "₹1.14 crore"],
    ], [1.0, 4.2, 2.4])
    p(doc, "The first-year SIM contract value is approximately ₹1.54 crore after including two one-time implementation engagements of ₹20 lakh each. The recurring component remains ₹1.14 crore per year under the base price scenario. These are planning targets, not promises; they depend on pilot results, procurement approvals and authority adoption.")
    h(doc, "Judge perspective")
    p(doc, "A good SIH market plan must prove that the project has a buyer, a usable deployment path and a credible first customer. MovIqSense has all three: public transport authorities already invest in buses, cameras, GPS and Intelligent Transport Systems; municipalities need better defect and traffic visibility; and a small pilot can demonstrate value before citywide investment.")
    br(doc)

    # Page 3
    h(doc, "2 Methodology and Definitions")
    p(doc, "TAM, SAM and SIM are not three separate markets. They are three views of the same opportunity at different levels of reach. We use a bottom-up calculation because it lets reviewers inspect every assumption: number of buses, authority licences, annual subscription price and implementation cost.")
    tbl(doc, ["Term", "Meaning Used by MovIqSense", "Why It Is Useful"], [
        ["TAM - Total Addressable Market", "The long-term revenue opportunity if MovIqSense is adopted by the relevant high-potential public and city-bus fleet universe.", "Shows the strategic ceiling without claiming every Indian vehicle as an immediate customer."],
        ["SAM - Serviceable Available Market", "The near-term segment compatible with the product and policy environment: connected city fleets, e-bus programmes and Smart City operations.", "Shows where the product can realistically compete with its current capability."],
        ["SIM - Serviceable Immediately Obtainable Market", "The first 36-month segment a student-origin team can target through pilots, BEL ecosystem support and early city partnerships.", "Shows a credible first commercial beachhead. This is similar to the standard SOM concept."],
    ], [1.5, 3.8, 2.3])
    h(doc, "Base commercial assumptions")
    tbl(doc, ["Input", "Assumption", "Reasoning"], [
        ["Annual per-bus software fee", "₹42,000 per bus per year", "₹3,500 per bus per month for AI event processing, health monitoring and standard dashboard use; lower than the pilot cost because shared platform costs reduce at scale."],
        ["Authority analytics licence", "₹15-30 lakh per authority per year", "Covers GIS dashboard, role-based users, reporting, priority workflow and integration support."],
        ["Initial implementation fee", "₹20-25 lakh per authority", "Covers onboarding, interface integration, user training, data migration and acceptance testing."],
        ["Revenue basis", "Annual recurring revenue plus separate initial implementation", "Prevents one-time deployment revenue from being incorrectly presented as subscription income."],
    ], [1.65, 1.6, 4.35])
    p(doc, "All rupee values are approximate planning values in current-price terms. They must be validated through GeM comparisons, competitive quotations, tax treatment, state procurement rules and the actual availability of cameras, GPS/AVL and data connectivity.")
    br(doc)

    # Page 4
    h(doc, "3 Evidence Base and Market Signals")
    p(doc, "The report uses public programme data as a market signal, not as proof that every bus is already available for procurement. PM-eBus Sewa provides the most relevant official reference because it links city buses with technology-driven mobility infrastructure. The scheme has a 10,000 e-bus deployment target, covers urban areas, and includes Intelligent Transit Management System context. This supports the thesis that a software layer such as MovIqSense can be positioned alongside fleet and city mobility systems.")
    tbl(doc, ["Public Signal", "Reported Detail", "Relevance"], [
        ["PM-eBus Sewa", "10,000 e-buses planned under the PPP model; programme materials refer to city operations and Intelligent Transit Management Systems.", "Defines a credible initial addressable city-bus opportunity."],
        ["PM-eBus Sewa scale", "Cabinet-approved scheme cost of ₹57,613 crore, with ₹20,000 crore central support.", "Shows that public transport is a significant government infrastructure and technology domain."],
        ["Road safety need", "MoRTH reported 4,80,583 accidents and 1,72,890 fatalities in 2023.", "Supports demand for earlier hazard visibility, incident evidence and better road-safety intelligence."],
        ["Existing asset base", "Buses increasingly carry cameras and GPS/AVL for operations and safety.", "MovIqSense can reuse compatible equipment instead of asking cities to build a new camera network."],
    ], [1.45, 3.45, 2.7])
    h(doc, "What we do not assume")
    for item in [
        "We do not assume that every bus in PM-eBus Sewa has a compatible camera interface on day one.",
        "We do not assume that every city will procure a new AI platform immediately.",
        "We do not claim that AI output alone can enforce traffic violations or replace human decision-making.",
        "We do not treat old national bus-fleet counts as current commercial demand without a fresh authority-level fleet audit.",
    ]:
        bullet(doc, item)
    p(doc, "This discipline matters in SIH: a smaller, defensible market model is more impressive than a large number with no connection to delivery capacity.")
    br(doc)

    # Page 5 TAM
    h(doc, "4 Total Addressable Market TAM")
    p(doc, "TAM represents the long-term opportunity if MovIqSense becomes a standard intelligence layer across a focused universe of 50,000 high-potential public and city-fleet buses. This is a planning universe, not an official fleet count. It includes large State Transport Undertaking fleets, municipal buses, contracted city fleets and connected public-service vehicles in high-value urban corridors. It deliberately excludes private cars, two-wheelers and rural fleets with no near-term technology fit.")
    tbl(doc, ["TAM Calculation", "Formula", "Value"], [
        ["Bus software subscriptions", "50,000 buses × ₹42,000 per year", "₹210 crore ARR"],
        ["Authority analytics licences", "70 authorities × ₹30 lakh per year", "₹21 crore ARR"],
        ["Total recurring TAM", "₹210 crore + ₹21 crore", "₹231 crore ARR"],
        ["Initial integration services", "50 authorities × ₹25 lakh one time", "₹12.5 crore one-time opportunity"],
    ], [2.1, 3.1, 2.4])
    h(doc, "Why 50,000 buses is a sensible planning universe")
    p(doc, "MovIqSense is intended for fleets that generate daily route coverage, can support some level of camera or GPS integration, and have a government or public-service use case. Fifty thousand is therefore a deliberately filtered opportunity, not a claim about every bus in India. It gives the project a meaningful national growth path while keeping the market estimate tied to the real conditions required for deployment.")
    h(doc, "TAM value proposition")
    for item in [
        "A per-bus platform model matches how fleet technology is budgeted and monitored.",
        "An authority licence pays for shared GIS, role management, reporting and cross-fleet analytics.",
        "One-time integration revenue supports deployment without inflating the recurring market estimate.",
        "TAM can expand later to municipal, sanitation, inspection and emergency fleets where policy allows."]:
        bullet(doc, item)
    br(doc)

    # Page 6 SAM
    h(doc, "5 Serviceable Available Market SAM")
    p(doc, "SAM is the market MovIqSense can serve with its present product architecture: AI video detection, browser or edge-camera input, GPS telemetry, event APIs, a GIS dashboard, traffic analysis, defect workflow and authorised incident evidence. The most relevant starting pool is 10,000 PM-eBus Sewa buses and comparable digitally enabled city operations. These fleets are closer to the required operational environment than the broader national bus universe.")
    tbl(doc, ["SAM Calculation", "Formula", "Value"], [
        ["Bus software subscriptions", "10,000 buses × ₹42,000 per year", "₹42 crore ARR"],
        ["Authority analytics licences", "30 authorities × ₹20 lakh per year", "₹6 crore ARR"],
        ["Total recurring SAM", "₹42 crore + ₹6 crore", "₹48 crore ARR"],
        ["Initial integration services", "30 authorities × ₹25 lakh one time", "₹7.5 crore one-time opportunity"],
    ], [2.1, 3.1, 2.4])
    h(doc, "SAM customer profile")
    table_data = [
        ["State Transport Undertaking", "Fleet monitoring, route safety, driver and vehicle visibility", "Per-bus subscription and fleet dashboard"],
        ["Smart City ICCC", "GIS incident map, road-condition intelligence, alert aggregation", "Authority analytics licence and API integration"],
        ["Municipal/PWD team", "Prioritised potholes, waterlogging and repair closure", "Workflow users within authority licence"],
        ["Traffic police", "Accident alert, controlled evidence access and hotspot visibility", "Authorised role-based dashboard access"],
    ]
    tbl(doc, ["Customer", "Primary Need", "Commercial Offer"], table_data, [1.6, 3.25, 2.75])
    p(doc, "The SAM estimate is intentionally limited to organisations where MovIqSense is a natural extension of an existing transport, GIS, command-centre or road-maintenance workflow. This improves commercial credibility because the buyer and procurement logic are visible from the beginning.")
    br(doc)

    # Page 7 SIM
    h(doc, "6 Serviceable Immediately Obtainable Market SIM")
    p(doc, "For this report, SIM means the first market that MovIqSense can realistically pursue after prototype validation. It is the equivalent of the first achievable SOM segment, but we use the user-requested term SIM. We propose two early-adopter authorities, each connecting around 100 buses after a controlled 10-bus proof of concept. This is an ambitious but feasible 36-month target if the pilot results are strong and a BEL, STU or Smart City partner supports implementation.")
    tbl(doc, ["SIM Calculation", "Formula", "Value"], [
        ["Bus subscriptions", "200 buses × ₹42,000 per year", "₹84 lakh ARR"],
        ["Authority licences", "2 authorities × ₹15 lakh per year", "₹30 lakh ARR"],
        ["Total recurring SIM", "₹84 lakh + ₹30 lakh", "₹1.14 crore ARR"],
        ["Initial implementation", "2 authorities × ₹20 lakh one time", "₹40 lakh one-time"],
        ["First-year contract value", "₹1.14 crore + ₹40 lakh", "₹1.54 crore"],
    ], [2.1, 3.1, 2.4])
    h(doc, "Why this is more credible than claiming a citywide launch")
    p(doc, "Government software is adopted through trust, field evidence and procurement cycles. A 200-bus SIM recognises that a student team must first prove camera compatibility, model performance, network behaviour, officer adoption and maintenance workflow. It gives MovIqSense a practical sequence: prototype, 10-bus pilot, two 100-bus deployments, then wider city or state expansion.")
    h(doc, "SIM success conditions", 2)
    for item in [
        "At least one approved STU or Smart City pilot partner.",
        "Defined acceptance metrics for alert accuracy, latency, uptime and officer response.",
        "Access to existing camera and GPS feeds wherever possible.",
        "A documented data-governance and authorised evidence-review process.",
        "A reference case study showing verified road defects or incident workflow value."]:
        bullet(doc, item)
    br(doc)

    # Page 8 Pricing / unit economics
    h(doc, "7 Pricing and Unit Economics")
    p(doc, "The pricing model is Government B2G Software as a Service plus integration and annual support. It separates recurring platform value from one-time project work. This is important because authorities need predictable operating cost, while the solution provider needs funds for onboarding, integration and support.")
    tbl(doc, ["Revenue Component", "Base Price", "Included Value"], [
        ["Per-bus annual subscription", "₹42,000 per bus per year", "AI event processing, bus health, standard alerting, data retention baseline and fleet visibility."],
        ["Authority analytics licence", "₹15-30 lakh per year", "GIS dashboard, user roles, road-defect priority workflow, reports and cross-fleet analytics."],
        ["Initial implementation", "₹20-25 lakh per authority", "Camera/GPS assessment, integration, configuration, training, acceptance testing and launch support."],
        ["Annual maintenance and model update", "15-20% of implementation value or bundled enterprise support", "Security updates, monitoring, bug fixes, model maintenance and helpdesk support."],
        ["Optional analytics package", "Quoted after pilot", "Heat maps, origin-destination patterns, route-delay analytics and custom authority reports."],
    ], [2.0, 1.5, 4.1])
    h(doc, "Pilot economics versus scale economics", 2)
    p(doc, "The first ten buses cost more per unit because the pilot carries platform setup, field testing and integration learning. At 50 to 100 buses, the same dashboard, database, alert engine and operator training material are shared across more vehicles. This is why the ₹42,000 subscription price is a scale target, not a claim that a ten-bus pilot is immediately profitable. The pilot is an evidence-generating investment.")
    br(doc)

    # Page 9 cost control
    h(doc, "8 High Cost Challenges and How We Overcome Them")
    p(doc, "The biggest mistake in a video-AI proposal is to assume that cloud processing, storage and connectivity are free. They are not. Our cost-control strategy is part of the product design. It makes MovIqSense more suitable for public transport budgets and unreliable field connectivity.")
    tbl(doc, ["Cost Driver", "Potential Problem", "MovIqSense Response"], [
        ["Edge hardware", "Buying a high-end AI computer and new cameras for every bus can make the pilot unaffordable.", "Reuse compatible existing cameras; begin with a front-facing stream; use Jetson Orin Nano-class or equivalent hardware only where required."],
        ["Data and cloud storage", "Continuous HD video upload creates recurring data and storage bills.", "Run inference at or near the bus; send JSON events and selected evidence clips; use depot Wi-Fi for non-urgent sync."],
        ["GPS duplication", "Buying trackers even where an AVL feed already exists wastes capital.", "Integrate existing authorised GPS/AVL APIs first; use fallback tracker only where necessary."],
        ["False alerts", "Poor quality alerts create staff workload and unnecessary inspections.", "Use confidence filters, temporal confirmation, map clustering, multi-bus verification and human review."],
        ["Multi-camera expansion", "Front, rear and side streams increase compute and installation complexity.", "Validate one road-facing stream in the pilot, then add streams based on use case and measured load."],
        ["Vendor lock-in", "Closed systems can raise long-term contract cost.", "Use REST APIs, structured JSON, documented data export and authority data ownership."],
    ], [1.45, 2.7, 3.45])
    p(doc, "This approach does not remove all cost. It makes each rupee spent traceable to a field outcome: a useful detection, a reliable location, a faster response or a lower operating cost at fleet scale.")
    br(doc)

    # Page 10 GTM
    h(doc, "9 Go To Market Plan")
    p(doc, "MovIqSense should enter the government market through a pilot and not through a broad sales claim. The strongest path is to use the SIH prototype as a demonstration asset, seek a controlled technical partner, measure value, publish an internal pilot report and use that report to support the next procurement discussion.")
    tbl(doc, ["Phase", "Timeframe", "Customer and Activity", "Proof Required"], [
        ["Prototype validation", "0-3 months", "Demonstrate video detection, GPS, GIS event, accident evidence and road-defect workflow to BEL, STU and Smart City stakeholders.", "Working demo and clear limitation statement."],
        ["Technical pilot", "3-6 months", "2-3 buses on one corridor; validate camera interfaces, power, network and event quality.", "Installation acceptance, uptime and sample alert review."],
        ["Operational pilot", "6-12 months", "10 buses across two corridors with transport, PWD and traffic users.", "Verified defects, response-time comparison, officer feedback and cost data."],
        ["SIM conversion", "12-36 months", "Two 100-bus authority deployments with dashboard licence and integration scope.", "Formal procurement, service support plan and data-governance controls."],
    ], [1.25, 1.1, 3.2, 2.1])
    h(doc, "Procurement-friendly offer", 2)
    for item in [
        "A fixed-scope 10-bus proof of concept with agreed acceptance criteria.",
        "A subscription that can be increased or reduced by active bus count.",
        "Open API documentation and exportable event records for authority ownership.",
        "Role-based access and evidence handling, not unverified automated enforcement.",
        "Quarterly impact review based on verified outcomes rather than dashboard screenshots alone."]:
        bullet(doc, item)
    br(doc)

    # Page 11 Sensitivity
    h(doc, "10 Sensitivity Analysis and Risk Boundaries")
    p(doc, "Market sizing is useful only when the team shows what could change it. The following scenarios test the SIM estimate against adoption, pricing and delivery conditions. They help a judge see that the team has thought about both upside and risk.")
    tbl(doc, ["Scenario", "Fleet and Licence Assumption", "Recurring Revenue", "Interpretation"], [
        ["Conservative", "100 buses; 1 authority licence at ₹15 lakh", "₹57 lakh ARR", "One authority converts after pilot; still a viable reference deployment."],
        ["Base SIM", "200 buses; 2 authority licences at ₹15 lakh", "₹1.14 crore ARR", "Target for two early-adopter deployments within 36 months."],
        ["Growth case", "500 buses; 3 authority licences at ₹20 lakh", "₹2.70 crore ARR", "Possible only after field validation and a repeatable installation model."],
    ], [1.35, 3.2, 1.4, 1.65])
    h(doc, "Key risks that remain")
    for item in [
        "Procurement cycles can be longer than the technical build cycle.",
        "Model quality must be validated on local roads, rain, shadows and camera angles.",
        "A city may require integration with a legacy command system before approval.",
        "Hardware availability and exchange-rate movement can affect edge device cost.",
        "Privacy and number-plate evidence require authorised handling and human verification."]:
        bullet(doc, item)
    p(doc, "Our mitigation is phased deployment. We spend little before a technical assessment, validate on a few buses before ordering at scale, and convert only those results that improve an actual authority workflow into commercial claims.")
    br(doc)

    # Page 12 Conclusion sources
    h(doc, "11 Conclusion and SIH Recommendation")
    p(doc, "MovIqSense has a credible route from student prototype to government technology deployment because the buyer, the operating asset and the delivery workflow are already visible. Transport authorities own or manage bus fleets. Smart City and municipal teams need location-based road and incident intelligence. The platform is designed to reuse existing cameras and GPS where possible, which makes its first pilot financially more practical than building a new fixed-camera network.")
    p(doc, "The market model is intentionally conservative. TAM of ₹231 crore annually shows a meaningful long-term opportunity. SAM of ₹48 crore annually focuses on buses and authorities most compatible with the current product. SIM of ₹1.14 crore in recurring revenue identifies a realistic first commercial target: two 100-bus deployments following a successful pilot. The figures are not promises; they are a disciplined plan for what to validate next.")
    h(doc, "What we would ask an SIH judge to evaluate")
    for item in [
        "Does the pilot show a real chain from camera to geo-tagged event to government action?",
        "Can the team prove alert usefulness and not just visual detection?",
        "Can the system lower monitoring cost by reusing buses, cameras, GPS and event-based data transfer?",
        "Can the project be piloted with a willing authority and then scaled through measurable results?"]:
        bullet(doc, item)
    h(doc, "Sources and notes")
    sources = [
        "PM-eBus Sewa portal, Ministry of Housing and Urban Affairs: programme context, 10,000 e-bus target and Intelligent Transit Management System support. https://pm-ebus-sewa.mohua.gov.in/",
        "Prime Minister of India, Cabinet approval for PM-eBus Sewa: 10,000 e-buses in 169 cities and ₹57,613 crore total scheme cost. https://www.pmindia.gov.in/en/news_updates/cabinet-approves-pm-ebus-sewa-for-augmenting-city-bus-operations-priority-to-cities-having-no-organized-bus-service/",
        "Ministry of Road Transport and Highways, Road Accidents in India 2023: national accident and fatality statistics. https://morth.nic.in/sites/default/files/Road-Accident-in-India-2023-Publications.pdf",
        "All bus counts beyond the official PM-eBus reference, pricing, licensing, TAM, SAM and SIM figures are transparent internal planning assumptions prepared for SIH evaluation. They require authority fleet audits and formal quotations before procurement."]
    for item in sources:
        bullet(doc, item)

    doc.core_properties.title = "MovIqSense TAM SAM SIM Market Opportunity Report"
    doc.core_properties.author = "MetaMinds 2.0"
    doc.core_properties.subject = "SIH 2026 Problem Statement 26124"
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
