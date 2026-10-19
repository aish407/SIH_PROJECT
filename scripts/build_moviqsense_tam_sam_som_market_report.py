from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "docs" / "MovIqSense_TAM_SAM_SOM_Market_and_Growth_Report.docx"
NAVY, BLUE, PALE, TEXT, BORDER, GREY = "132238", "1F4E79", "F5F9FC", "1F2937", "D9E2F3", "667085"


def add_run(p, text, bold=False, size=10.1, color=TEXT):
    r = p.add_run(text)
    r.bold = bold
    r.font.name = "Aptos"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos")
    r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos")
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    return r


def style_cell(cell, color="FFFFFF"):
    props = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), color); props.append(shd)
    borders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:val"), "single"); edge.set(qn("w:sz"), "6"); edge.set(qn("w:color"), BORDER)
        borders.append(edge)
    props.append(borders)
    margins = OxmlElement("w:tcMar")
    for side in ("top", "start", "bottom", "end"):
        edge = OxmlElement(f"w:{side}")
        edge.set(qn("w:w"), "100"); edge.set(qn("w:type"), "dxa"); margins.append(edge)
    props.append(margins)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def p(doc, text, size=10.1, after=5):
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(after)
    para.paragraph_format.line_spacing = 1.12
    add_run(para, text, size=size)
    return para


def h(doc, text, level=1):
    para = doc.add_paragraph(style=f"Heading {level}")
    para.paragraph_format.space_before = Pt(8 if level == 1 else 5)
    para.paragraph_format.space_after = Pt(3)
    r = para.add_run(text); r.bold = True; r.font.name = "Aptos Display"
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display"); r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    r.font.size = Pt(14 if level == 1 else 11.3); r.font.color.rgb = RGBColor(0, 0, 0)
    return para


def bullet(doc, text):
    para = doc.add_paragraph(style="List Bullet")
    para.paragraph_format.space_after = Pt(2); para.paragraph_format.line_spacing = 1.02
    add_run(para, text, size=9.65)
    return para


def table(doc, headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers)); t.autofit = False; t.style = "Table Grid"
    trpr = t.rows[0]._tr.get_or_add_trPr(); repeat = OxmlElement("w:tblHeader"); repeat.set(qn("w:val"), "true"); trpr.append(repeat)
    for i, value in enumerate(headers):
        cell = t.rows[0].cells[i]; cell.width = Inches(widths[i]); style_cell(cell, NAVY)
        add_run(cell.paragraphs[0], value, bold=True, size=8.55, color="FFFFFF")
    for ri, values in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(values):
            cell = cells[i]; cell.width = Inches(widths[i]); style_cell(cell, "FFFFFF" if ri % 2 == 0 else PALE)
            cell.paragraphs[0].paragraph_format.space_after = Pt(0)
            add_run(cell.paragraphs[0], str(value), size=8.4)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t


def br(doc): doc.add_page_break()


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document(); sec = doc.sections[0]
    sec.top_margin, sec.bottom_margin = Inches(0.6), Inches(0.58); sec.left_margin, sec.right_margin = Inches(0.68), Inches(0.68)
    doc.styles["Normal"].font.name = "Aptos"; doc.styles["Normal"].font.size = Pt(10.1)
    footer = sec.footer.paragraphs[0]; footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(footer, "MovIqSense | Market and Growth Report | Confidential planning document", size=8, color=GREY)

    # 1 cover
    for _ in range(5): doc.add_paragraph()
    title = doc.add_paragraph(style="Title"); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("MovIqSense"); r.bold = True; r.font.name = "Aptos Display"; r.font.size = Pt(34); r.font.color.rgb = RGBColor(0, 0, 0)
    r._element.rPr.rFonts.set(qn("w:ascii"), "Aptos Display"); r._element.rPr.rFonts.set(qn("w:hAnsi"), "Aptos Display")
    sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(sub, "TAM SAM SOM Market and Growth Report", bold=True, size=17, color=BLUE)
    sub = doc.add_paragraph(); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(sub, "AI Powered Mobile Urban Intelligence Platform Using Public Transport Fleet", size=11.7)
    for _ in range(4): doc.add_paragraph()
    table(doc, ["Document scope", "Value"], [
        ["Product", "MovIqSense - fleet-based road, safety and traffic intelligence platform."],
        ["Primary market", "Public transport operators, Smart City operations, municipal road authorities and traffic-management agencies."],
        ["Commercial model", "Per-bus annual platform subscription, authority analytics licence, one-time implementation and enterprise support."],
        ["Market terms", "TAM: Total Addressable Market; SAM: Serviceable Available Market; SOM: Serviceable Obtainable Market."],
        ["Planning position", "All revenue values are assumption-led planning estimates, not a tender quotation, market guarantee or audited forecast."],
    ], [2.05, 5.45])
    br(doc)

    # 2 summary
    h(doc, "1 Market Summary")
    p(doc, "MovIqSense addresses a specific public-sector technology gap: buses already cover the roads that authorities need to monitor, but their camera and GPS systems are usually used only for recording or fleet visibility. The product converts those distributed assets into a structured stream of road-condition, traffic-density and incident observations for authorised government users.")
    p(doc, "The market opportunity is strongest where public fleets already have a digital operating environment: cameras, GPS or AVL, route management, an operations centre and a road-maintenance or traffic-management counterpart. The first commercial objective is therefore not to sell to every vehicle operator. It is to win a controlled public-fleet deployment, prove measurable operating value, and expand through the authority and its connected city ecosystem.")
    table(doc, ["Market layer", "Definition", "Base recurring revenue estimate"], [
        ["TAM", "50,000 high-potential public and city-fleet buses plus 70 authority analytics licences.", "Rs 231 crore per year"],
        ["SAM", "10,000 digitally ready e-bus and comparable city-fleet buses plus 30 authority licences.", "Rs 48 crore per year"],
        ["SOM", "200 buses and two early-adopter authorities within 36 months after a validated pilot.", "Rs 1.14 crore per year"],
    ], [1.0, 4.25, 2.25])
    p(doc, "The recurring estimates exclude one-time implementation income. Under the base SOM case, two implementation engagements of Rs 20 lakh each create an indicative first-year contract value of Rs 1.54 crore. The subscription component remains the core of the long-term business model because it funds model operations, support and product improvement.")
    br(doc)

    # 3 market drivers
    h(doc, "2 Market Drivers")
    p(doc, "The urban mobility market is moving toward connected fleets, digital ticketing, electric-bus operations, command centres and data-led service management. MovIqSense fits this direction because it does not require authorities to choose between mobility operations and road intelligence. It connects them through the same bus movement and the same operational route network.")
    table(doc, ["Driver", "Evidence or signal", "Commercial implication"], [
        ["Connected city fleets", "PM eBus Sewa targets 10,000 e-buses under a PPP model and includes ITMS context.", "Creates a relevant segment where fleet systems and digital operations are already part of the programme environment."],
        ["Road safety need", "MoRTH reported 4,80,583 road accidents and 1,72,890 fatalities during 2023.", "Increases the value of earlier hazard visibility and controlled incident evidence."],
        ["Distributed coverage", "Buses travel repeated routes across different road types and time periods.", "Allows observation coverage to grow with fleet deployment rather than new fixed-camera sites."],
        ["Pressure on maintenance teams", "Defects and waterlogging are often identified through reactive channels.", "Supports a ranked, geo-tagged maintenance queue rather than unstructured complaint intake."],
        ["Budget scrutiny", "Public agencies require traceable benefits and predictable operating cost.", "Favors an event-first, reusable-camera and phased subscription model."],
    ], [1.45, 3.1, 2.95])
    p(doc, "The commercial message should remain grounded: MovIqSense is not sold as a universal surveillance system. It is positioned as an operational intelligence layer that makes existing public-transport assets more useful to transport, road and traffic teams.")
    br(doc)

    # 4 customer segmentation
    h(doc, "3 Customer Segmentation and Buyer Map")
    p(doc, "MovIqSense has multiple users but a small number of economic buyers. Clear segmentation avoids a common B2G problem where a technically interested department has no budget, while the budget holder sees no direct operational benefit.")
    table(doc, ["Segment", "Economic buyer", "Primary pain point", "Offer"], [
        ["State Transport Undertakings", "MD, IT head, fleet operations head", "Limited value extracted from on-bus cameras; fragmented fleet visibility.", "Per-bus platform, fleet operations dashboard and API integration."],
        ["Municipal road and PWD departments", "Commissioner, engineering head, maintenance manager", "Late or duplicate defect reporting and weak repair prioritisation.", "Infrastructure intelligence module and workflow licence."],
        ["Smart City ICCCs", "CEO, command centre lead, city IT team", "Fixed CCTV coverage does not represent all corridors.", "GIS event feed, role-based analytics and system integrations."],
        ["Traffic police and traffic management", "Traffic commissioner or authorised operations lead", "Limited time to review incident signals and congestion context.", "Authorised incident evidence and traffic-analysis access."],
        ["Public-sector systems integrators", "Programme and business lead", "Need modular applications for mobility and city projects.", "White-label or integration partnership with documented APIs."],
    ], [1.45, 1.8, 2.55, 1.7])
    p(doc, "The preferred first buyer is an STU or city transport authority with an identifiable fleet and an existing GPS or camera estate. Municipal and traffic users become supporting stakeholders because they receive the downstream intelligence that makes the transport investment more valuable.")
    br(doc)

    # 5 value prop
    h(doc, "4 Value Proposition and Product Positioning")
    p(doc, "MovIqSense should be positioned as a mobile urban intelligence platform, not simply a computer-vision product. A model detects an object; a platform associates that observation with a bus, place, time, confidence, evidence and operational owner. This is the difference between a demonstration and a product that can fit a government workflow.")
    table(doc, ["Stakeholder", "Practical value", "Commercial proof point"], [
        ["Transport operator", "Uses fleet movement to understand road conditions, operational disruptions and vehicle activity along routes.", "Active buses, online state, route context and operational dashboard use."],
        ["Road maintenance team", "Receives a prioritised list of likely defects with repeat observations and map location.", "Verified defects per inspection trip and time from observation to case creation."],
        ["Traffic team", "Sees density patterns, vehicle mix and corridor pressure from moving fleet viewpoints.", "Coverage of route segments beyond fixed CCTV footprint."],
        ["Incident responder", "Receives timestamped, GPS-linked evidence for authorised review.", "Alert-to-review time and evidence completeness."],
        ["City leadership", "Gets a cross-department view of recurring safety and maintenance issues.", "Trend reports, hotspot maps and closure status."],
    ], [1.45, 3.55, 2.45])
    p(doc, "The strongest differentiation is cost-aware coverage. A bus already drives the corridor; therefore the product can collect observations while delivering transport service. This does not eliminate the need for fixed CCTV or inspections, but it makes the observation network more mobile and scalable.")
    br(doc)

    # 6 TAM
    h(doc, "5 Total Addressable Market TAM")
    p(doc, "TAM represents the long-term opportunity if MovIqSense becomes an intelligence layer across a focused universe of high-potential urban and public fleets. It is not an assertion that every bus in India is technically ready or commercially available. The 50,000-bus universe filters for city, public-service and contracted fleets where camera, GPS or operational-system integration is plausible.")
    table(doc, ["TAM component", "Calculation", "Annual value"], [
        ["Fleet subscriptions", "50,000 buses x Rs 42,000 per bus per year", "Rs 210 crore"],
        ["Authority analytics licences", "70 authorities x Rs 30 lakh per year", "Rs 21 crore"],
        ["Total recurring TAM", "Rs 210 crore + Rs 21 crore", "Rs 231 crore"],
        ["Implementation services", "50 authorities x Rs 25 lakh one time", "Rs 12.5 crore one time"],
    ], [2.0, 3.25, 2.2])
    p(doc, "The per-bus price is a scale assumption of Rs 3,500 per month. It is intended to cover event processing, fleet visibility, standard alerting, model operations and baseline support. The authority licence covers GIS, roles, reports, workflows and cross-fleet analytics. Separating these components prevents one-time integration revenue from being presented as recurring market size.")
    h(doc, "TAM boundary", 2)
    for item in [
        "Includes high-potential public, municipal and contracted city fleet operations where the product purpose fits.",
        "Excludes private personal vehicles, informal fleets and locations where no digital operating environment exists.",
        "Assumes product expansion through public-sector channels over time, not a one-year sales target.",
    ]: bullet(doc, item)
    br(doc)

    # 7 SAM
    h(doc, "6 Serviceable Available Market SAM")
    p(doc, "SAM narrows the opportunity to fleets that are closer to the present product architecture. This includes PM eBus Sewa-linked or comparable city operations with digital fleet management, probable camera or GPS access, and a nearby authority workflow that can use GIS events. The purpose of SAM is to show where MovIqSense can realistically sell before it has national deployment history.")
    table(doc, ["SAM component", "Calculation", "Annual value"], [
        ["Fleet subscriptions", "10,000 buses x Rs 42,000 per bus per year", "Rs 42 crore"],
        ["Authority analytics licences", "30 authorities x Rs 20 lakh per year", "Rs 6 crore"],
        ["Total recurring SAM", "Rs 42 crore + Rs 6 crore", "Rs 48 crore"],
        ["Implementation services", "30 authorities x Rs 25 lakh one time", "Rs 7.5 crore one time"],
    ], [2.0, 3.25, 2.2])
    table(doc, ["SAM qualification test", "Why it matters"], [
        ["Defined public fleet and operating routes", "Allows reliable bus identity, map association and recurring coverage."],
        ["Camera or GPS source that can be assessed", "Reduces upfront hardware and integration risk."],
        ["Named authority workflow", "Ensures events become maintenance, traffic or incident action rather than passive data."],
        ["Digital procurement path", "Allows a PoC, system integration or operational service contract."],
    ], [2.55, 4.9])
    p(doc, "SAM should be approached corridor by corridor. A city may have a large bus fleet but still be unsuitable for an immediate pilot if camera access, operational ownership or the maintenance response process is unclear.")
    br(doc)

    # 8 SOM
    h(doc, "7 Serviceable Obtainable Market SOM")
    p(doc, "SOM is the first realistic revenue target, not a theoretical percentage of TAM. MovIqSense proposes two early-adopter authorities, each scaling from a ten-bus controlled pilot to approximately 100 buses after acceptance. This gives a first commercial footprint of 200 buses within 36 months.")
    table(doc, ["SOM component", "Calculation", "Value"], [
        ["Fleet subscriptions", "200 buses x Rs 42,000 per year", "Rs 84 lakh recurring"],
        ["Authority licences", "2 authorities x Rs 15 lakh per year", "Rs 30 lakh recurring"],
        ["Total recurring SOM", "Rs 84 lakh + Rs 30 lakh", "Rs 1.14 crore per year"],
        ["Implementation income", "2 authorities x Rs 20 lakh one time", "Rs 40 lakh"],
        ["First-year SOM contract value", "Recurring plus implementation", "Rs 1.54 crore"],
    ], [2.0, 3.25, 2.2])
    p(doc, "The 200-bus target is deliberately modest. It recognises field surveys, procurement timelines, officer training, local model validation and change management. A smaller credible SOM is commercially stronger than an unsupported claim of immediate nationwide deployment.")
    h(doc, "Conversion path", 2)
    for item in [
        "Demonstration and technical assessment of existing camera, GPS and command-centre environment.",
        "Two to three bus technical proof of concept on one corridor.",
        "Ten-bus operational pilot with agreed acceptance metrics and monthly review.",
        "One hundred bus authority contract when utility, data governance and support requirements are accepted.",
    ]: bullet(doc, item)
    br(doc)

    # 9 price
    h(doc, "8 Pricing Strategy and Revenue Model")
    p(doc, "The pricing design combines predictable annual platform cost with transparent setup work. Public-sector buyers need to know what is recurring, what is project-specific, and which costs depend on available fleet assets. A modular model also allows the authority to begin with road condition and expand to traffic, evidence or advanced analytics when operational use is proven.")
    table(doc, ["Revenue line", "Planning price", "Included value"], [
        ["Per-bus platform subscription", "Rs 42,000 per bus per year", "Event processing, bus status, standard model operations, baseline data retention and fleet visibility."],
        ["Authority analytics licence", "Rs 15-30 lakh per year", "GIS, roles, defect workflow, reports, priority queue and cross-fleet analytics."],
        ["Initial implementation", "Rs 20-25 lakh per authority", "Fleet assessment, integration, configuration, training and acceptance testing."],
        ["Enterprise support", "15-20 percent of implementation value or bundled", "Monitoring, updates, security maintenance, issue response and support governance."],
        ["Advanced analytics option", "Quoted after pilot", "Route delay studies, heat maps, origin-destination patterns and authority-specific reports."],
    ], [1.8, 1.55, 4.1])
    p(doc, "Early pilots may have a higher cost per bus because platform setup, field testing and training are shared across fewer units. The subscription estimate is therefore a scale price, not an assertion that a ten-bus pilot will be profitable. The pilot is an investment in evidence and a reference deployment.")
    br(doc)

    # 10 GTM
    h(doc, "9 Go To Market Strategy")
    p(doc, "The route to market is partnership-led and evidence-led. Selling directly to a large city before a field reference exists is difficult. MovIqSense should use a transport, Smart City or public-sector systems-integration partner to identify a bounded operational problem, demonstrate the workflow, and move through a controlled pilot into a measurable deployment.")
    table(doc, ["Stage", "Target activity", "Success measure"], [
        ["Market access", "Engage STUs, city transport authorities, ICCCs, municipal engineering teams and public-sector integrators.", "Named operational sponsor and a suitable corridor."],
        ["Discovery", "Conduct fleet camera/GPS audit, workflow mapping and policy discussion.", "Signed technical scope and acceptance criteria."],
        ["Pilot sale", "Offer a fixed-scope ten-bus demonstration with clear evidence and support limits.", "Installed buses, active users and weekly review cadence."],
        ["Value proof", "Measure useful alerts, coverage, response time and data use.", "Verified outcome report accepted by stakeholders."],
        ["Expansion", "Scale by bus count, route priority and authority module.", "Subscription renewal and additional corridor rollout."],
    ], [1.25, 3.75, 2.45])
    h(doc, "Channel priorities", 2)
    for item in [
        "Public-sector mobility and ITS integrators for access to existing deployments and tender ecosystems.",
        "Transport authorities for fleet data, operational sponsorship and bus-level rollout.",
        "Smart City command centres for cross-department GIS use and controlled event integration.",
        "Road-maintenance departments for measurable closure outcomes that support renewal.",
    ]: bullet(doc, item)
    br(doc)

    # 11 competition
    h(doc, "10 Competitive Landscape and Differentiation")
    p(doc, "MovIqSense will operate alongside existing systems rather than displacing all of them. Fixed CCTV vendors, fleet-management systems, manual road inspections, citizen-complaint platforms and standalone computer-vision tools each solve part of the problem. The commercial opportunity is to connect mobile observation with an authority workflow at a manageable operating cost.")
    table(doc, ["Alternative", "Strength", "MovIqSense differentiation"], [
        ["Fixed CCTV", "Continuous coverage at selected intersections.", "Extends visibility to corridors visited by buses and does not require a new pole or network at every location."],
        ["Fleet GPS systems", "Reliable fleet position and route operations.", "Adds visual road and safety intelligence to location data."],
        ["Manual inspection", "Human judgement and engineering accountability.", "Supplies a prioritised map of likely issues so inspection time is used more efficiently."],
        ["Citizen complaints", "Captures lived experience and local context.", "Adds repeated, timestamped field observation; can complement complaint systems rather than replace them."],
        ["Standalone AI video products", "Strong point detection on selected input.", "Combines model output with bus identity, GIS, workflow state, evidence and multi-department reporting."],
    ], [1.55, 2.65, 3.25])
    p(doc, "The defensible advantage is not a claim that a single model is perfect. It is the ability to operate a modular detection portfolio, associate results with fleet routes, control data cost, and turn observations into a traceable municipal action loop.")
    br(doc)

    # 12 financial / sources
    h(doc, "11 Three Year Commercial Plan and Assumptions")
    p(doc, "The following plan describes a disciplined growth path. It assumes that expansion is earned through successful operational pilots and that each authority adoption requires technical, commercial and governance approval. Values are rounded planning estimates in current-price terms and exclude GST.")
    table(doc, ["Year", "Deployment assumption", "Recurring revenue", "Implementation revenue", "Commercial focus"], [
        ["Year 1", "10-bus pilot and one authority licence", "Rs 19.2 lakh", "Rs 20 lakh", "Technical validation, workflow adoption and reference case."],
        ["Year 2", "100 buses and one authority licence", "Rs 57 lakh", "Rs 20 lakh", "First scale contract, route coverage and support process."],
        ["Year 3", "200 buses and two authority licences", "Rs 1.14 crore", "Rs 20 lakh", "Second authority conversion and repeatable rollout."],
    ], [0.8, 2.25, 1.35, 1.45, 2.0])
    h(doc, "Cost control for commercial viability", 2)
    for item in [
        "Reuse compatible cameras and authorised GPS/AVL before purchasing vehicle hardware.",
        "Use edge inference and event-first transfer; upload only selected clips and evidence instead of continuous HD video.",
        "Synchronise non-urgent media at depot Wi-Fi to control mobile-data cost.",
        "Use temporal confirmation and spatial clustering to reduce false-alert review and field-trip cost.",
        "Offer a modular deployment so a buyer pays first for the use cases it can operationally own.",
    ]: bullet(doc, item)
    h(doc, "Source notes", 2)
    for source in [
        "PM eBus Sewa portal, Ministry of Housing and Urban Affairs: 10,000 e-bus programme, ITMS context and deployment updates. https://pm-ebus-sewa.mohua.gov.in/",
        "Ministry of Road Transport and Highways, Road Accidents in India 2023: national accident, fatality and injury statistics. https://morth.nic.in/sites/default/files/Road-Accident-in-India-2023-Publications.pdf",
        "All TAM, SAM, SOM, pricing and growth values are transparent internal planning assumptions. They require fleet audit, competitive quotes, security review and procurement approval before commercial use.",
    ]:
        pp = doc.add_paragraph(style="List Bullet"); pp.paragraph_format.space_after = Pt(2); add_run(pp, source, size=8.45, color=GREY)
    p(doc, "MovIqSense has a focused commercial path: establish measurable value on a small public fleet, convert that proof into authority-level recurring revenue, and expand through connected transport and city operations. The market model is designed to be reviewed and refined with each real deployment.")

    doc.core_properties.title = "MovIqSense TAM SAM SOM Market and Growth Report"
    doc.core_properties.author = "MovIqSense Team"
    doc.core_properties.subject = "Market opportunity and commercial growth planning"
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
