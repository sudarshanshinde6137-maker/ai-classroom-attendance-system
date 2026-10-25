"""
Report Generator
Exports attendance data as Excel (.xlsx) and PDF reports
"""

import os
from datetime import datetime
from typing import List, Dict

REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "attendance_records"
)


def _ensure_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


# ── Excel Export ──────────────────────────────────────────────────────────────

def export_excel(records: List[Dict], date: str, summary: Dict) -> str:
    """Export attendance records to an Excel file. Returns file path."""
    import pandas as pd

    _ensure_dir()
    filename = f"Attendance_{date.replace('-', '_')}.xlsx"
    filepath = os.path.join(REPORTS_DIR, filename)

    df_records = pd.DataFrame(records)
    # Rename lowercase DB keys to display-friendly headers
    col_map = {
        "name": "Name", "roll_no": "Roll No", "prn": "PRN",
        "time": "Time", "status": "Status", "session": "Session", "subject": "Subject"
    }
    df_records = df_records.rename(columns=col_map)
    # Keep only the display columns in order (ignore any extra DB cols)
    display_cols = [c for c in ["Name", "Roll No", "PRN", "Time", "Status", "Session", "Subject"] if c in df_records.columns]
    df_records = df_records[display_cols]

    df_summary = pd.DataFrame([{
        "Date": date,
        "Total Students": summary["total"],
        "Present": summary["present"],
        "Absent": summary["absent"],
        "Attendance %": f"{(summary['present'] / summary['total'] * 100):.1f}%" if summary['total'] else "0%"
    }])

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
        df_records.to_excel(writer, sheet_name="Attendance", index=False)

        # Auto-width columns
        for sheet_name in writer.sheets:
            ws = writer.sheets[sheet_name]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col) + 4
                ws.column_dimensions[col[0].column_letter].width = min(max_len, 40)

    return filepath


# ── PDF Export ────────────────────────────────────────────────────────────────

def export_pdf(records: List[Dict], date: str, summary: Dict) -> str:
    """Export attendance report as a PDF. Returns file path."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, HRFlowable)

    _ensure_dir()
    filename = f"Attendance_{date.replace('-', '_')}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"],
                                  fontSize=18, spaceAfter=6,
                                  textColor=colors.HexColor("#1a237e"))
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"],
                                fontSize=10, textColor=colors.grey, spaceAfter=4)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"],
                                    fontSize=12, textColor=colors.HexColor("#1a237e"))

    elements = []

    # Title
    elements.append(Paragraph("🎓 Classroom Attendance Report", title_style))
    elements.append(Paragraph(f"Date: {date}  |  Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}", sub_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e")))
    elements.append(Spacer(1, 0.4*cm))

    # Summary box
    pct = f"{(summary['present'] / summary['total'] * 100):.1f}%" if summary['total'] else "0%"
    summary_data = [
        ["Total Students", "Present", "Absent", "Attendance %"],
        [str(summary["total"]), str(summary["present"]), str(summary["absent"]), pct]
    ]
    summary_table = Table(summary_data, colWidths=[4*cm]*4)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#e8eaf6"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.6*cm))

    # Attendance table
    elements.append(Paragraph("Attendance Details", heading_style))
    elements.append(Spacer(1, 0.2*cm))

    headers = ["#", "Name", "Roll No", "PRN", "Time", "Status", "Subject"]
    table_data = [headers]
    
    for i, r in enumerate(records, 1):
        status = r.get("Status", r.get("status", "Absent"))
        table_data.append([
            str(i),
            r.get("Name", r.get("name", "")),
            r.get("Roll No", r.get("roll_no", "")),
            r.get("PRN", r.get("prn", "")),
            r.get("Time", r.get("time", "--")),
            status,
            r.get("Subject", r.get("subject", "General"))
        ])

    col_widths = [1*cm, 4.2*cm, 2.7*cm, 3.1*cm, 2.2*cm, 2.0*cm, 3.0*cm]
    att_table = Table(table_data, colWidths=col_widths)

    # Row colors: green for present, red for absent
    row_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#283593")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#9fa8da")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_i, r in enumerate(records, 1):
        status = r.get("Status", r.get("status", "Absent"))
        if status == "Present":
            row_styles.append(("BACKGROUND", (0, row_i), (-1, row_i), colors.HexColor("#e8f5e9")))
            row_styles.append(("TEXTCOLOR", (-1, row_i), (-1, row_i), colors.HexColor("#2e7d32")))
        else:
            row_styles.append(("BACKGROUND", (0, row_i), (-1, row_i), colors.HexColor("#ffebee")))
            row_styles.append(("TEXTCOLOR", (-1, row_i), (-1, row_i), colors.HexColor("#c62828")))

    att_table.setStyle(TableStyle(row_styles))
    elements.append(att_table)

    # Footer
    elements.append(Spacer(1, cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Paragraph(
        "Generated by AI Classroom Attendance System",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                        textColor=colors.grey, alignment=1)
    ))

    doc.build(elements)
    return filepath


def export_csv(records: List[Dict], date: str) -> str:
    """Export as CSV."""
    import pandas as pd
    _ensure_dir()
    filename = f"Attendance_{date.replace('-', '_')}.csv"
    filepath = os.path.join(REPORTS_DIR, filename)
    df = pd.DataFrame(records)
    df.to_csv(filepath, index=False)
    return filepath


# ── Defaulter List Export ─────────────────────────────────────────────────────

def export_defaulters_report(defaulters: List[Dict], threshold: float = 75.0, format: str = "excel") -> str:
    """Export Defaulter Students (< 75%) to Excel or PDF."""
    _ensure_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "excel":
        import pandas as pd
        filename = f"Defaulters_Alert_{timestamp}.xlsx"
        filepath = os.path.join(REPORTS_DIR, filename)

        export_data = []
        for idx, s in enumerate(defaulters, 1):
            export_data.append({
                "#": idx,
                "Name": s.get("name", ""),
                "Roll No": s.get("roll_no", ""),
                "PRN": s.get("prn", ""),
                "Lectures Attended": s.get("attended", 0),
                "Total Lectures Held": s.get("total_held", 0),
                "Absent Count": s.get("absent", 0),
                "Attendance %": f"{s.get('percentage', 0.0):.1f}%",
                "Status": "CRITICAL DEFAULTER" if s.get("percentage", 0) < 60 else "DEFAULTER WARNING"
            })

        df = pd.DataFrame(export_data)
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Defaulters", index=False)
            ws = writer.sheets["Defaulters"]
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col) + 4
                ws.column_dimensions[col[0].column_letter].width = min(max_len, 35)

        return filepath

    # PDF Export
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer, HRFlowable)

    filename = f"Defaulters_Alert_{timestamp}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                             topMargin=1.8*cm, bottomMargin=1.8*cm,
                             leftMargin=1.8*cm, rightMargin=1.8*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("DefTitle", parent=styles["Title"],
                                  fontSize=17, spaceAfter=4,
                                  textColor=colors.HexColor("#b71c1c"))
    sub_style = ParagraphStyle("DefSub", parent=styles["Normal"],
                                fontSize=10, textColor=colors.grey, spaceAfter=8)
    alert_box_style = ParagraphStyle("AlertBox", parent=styles["Normal"],
                                     fontSize=11, fontName="Helvetica-Bold",
                                     textColor=colors.HexColor("#b71c1c"))

    elements = []
    elements.append(Paragraph("⚠️ Official Defaulter Attendance Notice", title_style))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}  |  Criteria: Attendance strictly below {threshold:.0f}%",
        sub_style
    ))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#b71c1c")))
    elements.append(Spacer(1, 0.4*cm))

    # Alert summary banner
    summary_msg = f"<b>ACTION REQUIRED:</b> {len(defaulters)} student(s) identified with attendance under {threshold:.0f}%. Students must meet faculty mentor."
    elements.append(Paragraph(summary_msg, alert_box_style))
    elements.append(Spacer(1, 0.4*cm))

    table_data = [["#", "Student Name", "Roll No", "PRN", "Attended", "Held", "Attendance %"]]
    for idx, d in enumerate(defaulters, 1):
        table_data.append([
            str(idx),
            d.get("name", ""),
            d.get("roll_no", ""),
            d.get("prn", ""),
            str(d.get("attended", 0)),
            str(d.get("total_held", 0)),
            f"{d.get('percentage', 0.0):.1f}%"
        ])

    col_widths = [1*cm, 4.5*cm, 3.0*cm, 3.2*cm, 2.0*cm, 1.8*cm, 2.5*cm]
    t = Table(table_data, colWidths=col_widths)

    row_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#b71c1c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#ef9a9a")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    for r_idx in range(1, len(table_data)):
        bg = colors.HexColor("#ffebee") if r_idx % 2 == 1 else colors.white
        row_styles.append(("BACKGROUND", (0, r_idx), (-1, r_idx), bg))
        row_styles.append(("TEXTCOLOR", (-1, r_idx), (-1, r_idx), colors.HexColor("#b71c1c")))
        row_styles.append(("FONTNAME", (-1, r_idx), (-1, r_idx), "Helvetica-Bold"))

    t.setStyle(TableStyle(row_styles))
    elements.append(t)

    doc.build(elements)
    return filepath


# ── Monthly Register Matrix Export ───────────────────────────────────────────

def export_monthly_matrix(matrix: Dict, format: str = "excel") -> str:
    """Export monthly register grid sheet (Students vs Days 1..31) to Excel."""
    import pandas as pd
    _ensure_dir()

    year = matrix.get("year", datetime.now().year)
    month = matrix.get("month", datetime.now().month)
    subject = matrix.get("subject", "All")
    held_days = matrix.get("held_days", [])
    rows = matrix.get("rows", [])

    filename = f"Register_Matrix_{year}_{month:02d}_{subject.replace(' ', '_')}.xlsx"
    filepath = os.path.join(REPORTS_DIR, filename)

    excel_rows = []
    for r in rows:
        row_dict = {
            "Roll No": r.get("roll_no", ""),
            "Student Name": r.get("name", ""),
            "PRN": r.get("prn", "")
        }
        # Add columns for each day of classes
        for day in held_days:
            col_name = f"Day {day:02d}"
            row_dict[col_name] = r["days"].get(day, "-")

        row_dict["Total Attended"] = r.get("attended", 0)
        row_dict["Total Held"] = r.get("total_held", 0)
        row_dict["Monthly %"] = f"{r.get('percentage', 0.0):.1f}%"
        excel_rows.append(row_dict)

    df = pd.DataFrame(excel_rows)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=f"{year}_{month:02d}", index=False)
        ws = writer.sheets[f"{year}_{month:02d}"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col) + 3
            ws.column_dimensions[col[0].column_letter].width = min(max_len, 28)

    return filepath
