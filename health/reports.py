"""In-memory PDF exports for a user's own recorded health information."""

from datetime import date
from html import escape
from io import BytesIO
import unicodedata

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _safe_text(value):
    """Escape text for ReportLab's paragraph markup and strip control chars."""
    text = "" if value is None else str(value)
    text = "".join(char for char in text if char in "\n\t" or unicodedata.category(char)[0] != "C")
    return escape(text).replace("\n", "<br/>") or "—"


def _table(headers, rows, styles):
    if not rows:
        return [Paragraph("No entries in this date range.", styles["BodyText"])]
    data = [[Paragraph(f"<b>{_safe_text(header)}</b>", styles["TableText"]) for header in headers]]
    data.extend([[Paragraph(_safe_text(value), styles["TableText"]) for value in row] for row in rows])
    table = Table(data, colWidths=[(A4[0] - 40 * mm) / len(headers)] * len(headers), repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f2ef")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f514d")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d6e0df")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [table]


def build_health_report(start, end, cycles, symptoms, lifestyle):
    """Build and return PDF bytes without writing private data to disk."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=18 * mm,
        title="PCOS Insight Health Record",
        author="PCOS Insight",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#236b66"), spaceAfter=8))
    styles.add(ParagraphStyle(name="SectionHeading", parent=styles["Heading2"], textColor=colors.HexColor("#236b66"), spaceBefore=13, spaceAfter=7, keepWithNext=True))
    styles.add(ParagraphStyle(name="TableText", parent=styles["BodyText"], fontSize=8.5, leading=11, wordWrap="CJK"))
    story = [
        Paragraph("PCOS Insight · Personal Health Record", styles["ReportTitle"]),
        Paragraph(f"Selected dates: {_safe_text(start.strftime('%d %b %Y'))} to {_safe_text(end.strftime('%d %b %Y'))}", styles["BodyText"]),
        Paragraph(f"Generated: {_safe_text(date.today().strftime('%d %b %Y'))}", styles["BodyText"]),
        Spacer(1, 8),
        Paragraph("Private health information. Store and share this report carefully.", styles["BodyText"]),
        Paragraph("Educational tracking record only. It is not a PCOS diagnosis, risk estimate, or substitute for assessment by a qualified clinician.", styles["BodyText"]),
        Paragraph("Cycle entries", styles["SectionHeading"]),
    ]
    story.extend(_table(
        ["Period start", "Period end", "Flow", "Notes"],
        [[entry.period_start, entry.period_end, entry.get_flow_display() or "Not recorded", entry.notes] for entry in cycles],
        styles,
    ))
    story.append(Paragraph("Symptom entries", styles["SectionHeading"]))
    story.extend(_table(
        ["Date", "Symptom", "Severity (1–5)", "Notes"],
        [[entry.recorded_on, entry.symptom, entry.severity, entry.notes] for entry in symptoms],
        styles,
    ))
    story.append(Paragraph("Lifestyle entries", styles["SectionHeading"]))
    story.extend(_table(
        ["Date", "Sleep (hours)", "Activity (minutes)", "Mood", "Notes"],
        [[entry.recorded_on, entry.sleep_hours, entry.activity_minutes, entry.get_mood_display() or "Not recorded", entry.notes] for entry in lifestyle],
        styles,
    ))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#65736f"))
        canvas.drawString(20 * mm, 10 * mm, "PCOS Insight · Private personal record")
        canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
