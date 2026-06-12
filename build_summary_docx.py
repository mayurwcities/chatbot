#!/usr/bin/env python3
"""Build a SHORT, non-technical client overview .docx."""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = "/Users/wcities/ReactStudy/chatbot"
OUT = os.path.join(SRC, "Venue-Chatbot-Overview-Plain-English.docx")

ACCENT = RGBColor(0x1F, 0x4E, 0x79)
TEAL = RGBColor(0x0E, 0x7C, 0x66)
GREY = RGBColor(0x55, 0x55, 0x55)
DARK = RGBColor(0x22, 0x22, 0x22)

doc = Document()
sec = doc.sections[0]
sec.left_margin = Inches(1.0)
sec.right_margin = Inches(1.0)

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11.5)
normal.paragraph_format.space_after = Pt(8)
normal.paragraph_format.line_spacing = 1.2

for lvl, sz in [(1, 17), (2, 13)]:
    st = doc.styles[f"Heading {lvl}"]
    st.font.name = "Calibri"
    st.font.size = Pt(sz)
    st.font.color.rgb = ACCENT
    st.font.bold = True


def shade(cell, hexc):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), hexc)
    tcPr.append(shd)


def para(text, size=11.5, color=DARK, bold=False, italic=False,
         align=None, space_after=8, space_before=0):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(space_before)
    r = p.add_run(text)
    r.font.size = Pt(size); r.font.color.rgb = color
    r.bold = bold; r.italic = italic
    return p


def bullet(text, bold_lead=None):
    p = doc.add_paragraph(style="List Bullet")
    if bold_lead:
        r = p.add_run(bold_lead + "  ")
        r.bold = True; r.font.color.rgb = ACCENT
    p.add_run(text)
    return p


def callout(title, body, fill="EAF1F8", bar="1F4E79"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    shade(cell, fill)
    cell.text = ""
    p1 = cell.paragraphs[0]
    r = p1.add_run(title)
    r.bold = True; r.font.size = Pt(11.5); r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    p2 = cell.add_paragraph()
    r2 = p2.add_run(body)
    r2.font.size = Pt(11); r2.font.color.rgb = DARK
    # left accent border
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single"); left.set(qn("w:sz"), "24")
    left.set(qn("w:space"), "0"); left.set(qn("w:color"), bar)
    borders.append(left)
    tcPr.append(borders)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def simple_table(header, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Light List Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True; r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF); r.font.size = Pt(11)
        shade(c, "1F4E79")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(v)
            r.font.size = Pt(10.5)
            if i == 0:
                r.bold = True
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


# ================= TITLE =================
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
t.paragraph_format.space_before = Pt(36)
r = t.add_run("The Venue Chatbot")
r.font.size = Pt(32); r.bold = True; r.font.color.rgb = ACCENT

para("Run your whole business by chatting with it.",
     size=15, color=GREY, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
para("A plain-English overview", size=11, color=GREY,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16)

# rule
rp = doc.add_paragraph()
rp.alignment = WD_ALIGN_PARAGRAPH.CENTER
pPr = rp._p.get_or_add_pPr()
pbdr = OxmlElement("w:pBdr")
bottom = OxmlElement("w:bottom")
bottom.set(qn("w:val"), "single"); bottom.set(qn("w:sz"), "6")
bottom.set(qn("w:space"), "1"); bottom.set(qn("w:color"), "1F4E79")
pbdr.append(bottom); pPr.append(pbdr)

# ================= THE PROBLEM =================
doc.add_heading("The problem, in one breath", level=1)
para("Imagine you own a small restaurant. To keep it running online, you're "
     "logging into eight different apps every week:")

for item in [
    "Your website builder (Squarespace, Wix…)",
    "DoorDash, Uber Eats, and Grubhub dashboards",
    "A reservation tool (OpenTable, Resy)",
    "An email tool (Mailchimp)",
    "Instagram, Google Business, and your POS",
]:
    bullet(item)

para("Change your hours for a holiday? You have to update it in all of them, "
     "by hand. Most owners simply give up and let half of them go stale. "
     "It's tedious, it's error-prone, and it eats hours every week.", space_after=10)

callout("Our promise",
        "One chat window. You type “We’re closed July 4th” "
        "— and it updates everywhere at once. That’s the whole product.")

# ================= HOW IT FEELS =================
doc.add_heading("What it actually feels like to use", level=1)
para("No menus, no forms, no settings screens to hunt through. You just talk "
     "to it like you'd text a very capable assistant:")

examples = [
    ("“Add a $14 truffle pasta to the dinner menu.”",
     "Done — it’s live on your site and delivery apps."),
    ("“We sold out of the salmon.”",
     "Marked unavailable everywhere in seconds."),
    ("“Send last month’s customers a 15% weekend offer.”",
     "“That reaches 487 people — want me to send it?”"),
    ("“How did last week’s promo do?”",
     "“31% opened it, 22 booked a table.”"),
]
for q, a in examples:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("You:  "); r.bold = True; r.font.color.rgb = ACCENT
    r2 = p.add_run(q); r2.italic = True
    p2 = doc.add_paragraph()
    p2.paragraph_format.left_indent = Inches(0.0)
    p2.paragraph_format.space_after = Pt(10)
    r3 = p2.add_run("It:    "); r3.bold = True; r3.font.color.rgb = TEAL
    p2.add_run(a)

# ================= WHY IT WORKS NOW =================
doc.add_heading("Why this is possible now (and wasn’t before)", level=1)
para("Three things changed recently that make this realistic today:")
bullet("AI assistants finally take actions reliably — not just chat, but actually doing the task correctly.",
       bold_lead="They work.")
bullet("They can read a photo of your paper menu and set you up in 5 minutes instead of hours of typing.",
       bold_lead="They see.")
bullet("DoorDash, Square, Booking.com and others now offer stable ways to plug in and sync automatically.",
       bold_lead="Apps connect.")

# ================= SAFETY =================
doc.add_heading("“But what if it makes a mistake?”", level=1)
para("Fair question — and it's the one we take most seriously. Anything "
     "that could cost money or erase data (sending a blast, deleting a menu, "
     "issuing a refund) always asks you to confirm first. Every change is "
     "logged and reversible, so nothing happens behind your back and nothing "
     "is ever truly lost.", space_after=10)
callout("In short",
        "It moves fast on the small stuff, and stops to double-check on "
        "anything that matters. You’re always in control.",
        fill="EAF6F1", bar="0E7C66")

doc.add_page_break()

# ================= THE PLAN =================
doc.add_heading("The plan: start narrow, expand carefully", level=1)
para("We're not trying to do everything on day one. We start with independent "
     "restaurants, get them to love it, then add new types of venues one at a "
     "time — only once the previous step is solid.")

simple_table(
    ["When", "What we add", "Goal"],
    [
        ["Months 1–3", "Chat + restaurant pages, fully safe", "First 5 restaurants live"],
        ["Months 4–6", "Email & text marketing", "Customers running campaigns"],
        ["Months 7–10", "DoorDash auto-sync + website widget", "15–25 venues"],
        ["Months 11–13", "Square checkout + hotels", "40 venues, hotels live"],
        ["Months 14–15", "Tickets for tours & events", "50 venues"],
        ["Months 16–18", "Self sign-up + more app connections", "50–100 venues"],
    ],
)

callout("Where this lands at ~18 months",
        "A working platform serving restaurants, hotels, and tour operators — "
        "proven across three venue types and ready for its next stage of growth.")

# ================= THE NUMBERS =================
doc.add_heading("The shape of the build", level=1)
para("Honest, grounded targets — no hype:")
bullet("A small, focused team of about 4–6 people.", bold_lead="Team:")
bullet("From 5 venues at month 3 to 50–100 by month 18, and around 200 by month 24.",
       bold_lead="Growth:")
bullet("Restaurants first, then hotels, then tours — each only after the last one works.",
       bold_lead="Sequence:")

# ================= WHAT IT IS NOT =================
doc.add_heading("What we are deliberately NOT building", level=1)
para("Being clear about the boundaries is what keeps this realistic:")
bullet("An AI that magically edits any website on the internet — that’s an unsolved research problem, not a product.")
bullet("A replacement for cash registers like Square or Toast — we sit on top of them, not against them.")
bullet("Our own from-scratch AI brain — we use the best existing ones (Claude/GPT) instead of trying to build a worse one.")
bullet("Everything for everyone at once — restaurants first, then expand.")

# ================= THE BET =================
doc.add_heading("The one-line bet", level=1)
callout("The thesis",
        "Small venue owners will happily trade eight clunky dashboards for one "
        "conversation. Whoever makes that conversation trustworthy and genuinely "
        "useful owns the relationship — and everything else syncs from there.",
        fill="EAF1F8", bar="1F4E79")

para("That's the whole idea. Simple to say, careful to build, and grounded in "
     "tools that finally exist in 2026.", italic=True, color=GREY, space_before=6)

# footer
footer = sec.footer
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fr = fp.add_run("The Venue Chatbot — Plain-English Overview")
fr.font.size = Pt(8); fr.font.color.rgb = GREY

doc.save(OUT)
print("Saved:", OUT)
