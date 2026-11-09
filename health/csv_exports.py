"""Build spreadsheet-safe CSV exports for personal health records."""

import csv
from io import StringIO


def _cell(value):
    if value is None:
        return ""
    text = str(value)
    # Spreadsheet applications may interpret untrusted text as a formula.
    if text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


def build_health_csv(cycles, symptoms, lifestyle):
    """Return UTF-8 CSV text with a common schema across record types."""
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["record_type", "date", "end_date", "value", "detail", "notes"])

    rows = []
    rows.extend((entry.period_start, "cycle", entry) for entry in cycles)
    rows.extend((entry.recorded_on, "symptom", entry) for entry in symptoms)
    rows.extend((entry.recorded_on, "lifestyle", entry) for entry in lifestyle)

    for _, record_type, entry in sorted(rows, key=lambda row: (row[0], row[1])):
        if record_type == "cycle":
            values = (record_type, entry.period_start, entry.period_end, entry.get_flow_display(), "", entry.notes)
        elif record_type == "symptom":
            values = (record_type, entry.recorded_on, "", entry.symptom, f"Severity {entry.severity}/5", entry.notes)
        else:
            details = []
            if entry.sleep_hours is not None:
                details.append(f"Sleep: {entry.sleep_hours} hours")
            if entry.activity_minutes is not None:
                details.append(f"Activity: {entry.activity_minutes} minutes")
            values = (record_type, entry.recorded_on, "", entry.get_mood_display(), "; ".join(details), entry.notes)
        writer.writerow([_cell(value) for value in values])

    return output.getvalue()
