# file: src/report_generator.py
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

def build_gri_pdf_report(
    project_name: str,
    indicator_data: dict,
    unit_label: str = "",
    include_monthly: bool = True,
    include_forecast: bool = True,
    include_anomalies: bool = True,
    logo_path: str = "assets/company_logo.png"
) -> io.BytesIO:
    """
    Build a GRI-style PDF report and return BytesIO.
    - project_name: "EGY-WOOD"
    - indicator_data: dict keyed by indicator e.g.
        {
          "energy": {"yearly": DataFrame, "monthly_df": DataFrame, "narrative": "...", "forecast": (yr, val)},
          "water": {...},
          ...
        }
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    # Small helpers
    def draw_footer(page_num: int):
        footer_y = 12 * mm
        c.setFont("Helvetica", 8)
        c.setFillGray(0.45)
        c.drawCentredString(width / 2, footer_y, f"{project_name} — GRI Report  •  Page {page_num}")

    def safe_draw_image(img_path, x, y, w, h):
        try:
            if os.path.exists(img_path):
                img = ImageReader(img_path)
                c.drawImage(img, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')
                return True
        except Exception:
            pass
        return False

    now = datetime.utcnow()
    title_font = "Helvetica-Bold"

    # --- Cover ---
    c.setFont(title_font, 22)
    c.drawCentredString(width / 2, height - 60, f"{project_name} — GRI Sustainability Report")
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, height - 82, f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}")
    c.drawCentredString(width / 2, height - 100, f"Unit: {unit_label}")
    # logo (top-right)
    safe_draw_image(logo_path, width - (40 * mm), height - (45 * mm), 36 * mm, 36 * mm)
    draw_footer(1)
    c.showPage()

    # --- Table of contents (simple) ---
    c.setFont(title_font, 14)
    c.drawString(40, height - 60, "Table of Contents")
    c.setFont("Helvetica", 10)
    y = height - 90
    toc_lines = ["1. Executive summary", "2. KPI Summary & Trends"]
    idx = 3
    for k in sorted(indicator_data.keys()):
        toc_lines.append(f"{idx}. {k.capitalize()} (topic section)")
        idx += 1
    toc_lines.append(f"{idx}. Annex (raw tables)")
    for line in toc_lines:
        c.drawString(56, y, line); y -= 14
    draw_footer(2)
    c.showPage()

    # --- Executive summary (aggregate) ---
    c.setFont(title_font, 14)
    c.drawString(40, height - 60, "Executive summary")
    c.setFont("Helvetica", 10)
    y = height - 90
    # produce simple top-line bullets from indicator_data
    for key, obj in indicator_data.items():
        yearly = obj.get("yearly")
        latest = None
        try:
            latest = yearly.sort_values("Year").iloc[-1]
            val = latest["total_value"]
            y_line = f"- {key.capitalize()}: latest {val:,.2f} {unit_label}"
        except Exception:
            y_line = f"- {key.capitalize()}: data summary not available"
        c.drawString(50, y, y_line); y -= 12
        if y < 80:
            draw_footer(3); c.showPage(); y = height - 90
    draw_footer(3)
    c.showPage()

    # --- Per-indicator sections ---
    page_num = 4
    for key, obj in indicator_data.items():
        c.setFont(title_font, 13)
        c.drawString(40, height - 60, f"{key.capitalize()} — KPI & Analysis")
        c.setFont("Helvetica", 10)
        y = height - 90

        # KPI table header
        c.drawString(40, y, "Year"); c.drawString(120, y, "Total"); c.drawString(240, y, "Anomaly")
        y -= 14

        yearly = obj.get("yearly")
        if yearly is not None:
            for _, r in yearly.iterrows():
                try:
                    c.drawString(40, y, str(int(r["Year"])))
                    c.drawString(120, y, f"{r['total_value']:,.2f} {unit_label}")
                    an = "Yes" if r.get("anomaly", False) else "No"
                    c.drawString(240, y, an)
                except Exception:
                    pass
                y -= 12
                if y < 100:
                    draw_footer(page_num); c.showPage(); page_num += 1; y = height - 90

        # narrative
        narrative = obj.get("narrative")
        if narrative:
            if y < 170:
                draw_footer(page_num); c.showPage(); page_num += 1; y = height - 90
            c.setFont("Helvetica-Bold", 11); c.drawString(40, y, "Narrative"); y -= 16
            c.setFont("Helvetica", 10)
            for para in str(narrative).split("\n"):
                # naive wrapping ~90 chars
                while len(para) > 90:
                    chunk = para[:90]; c.drawString(46, y, chunk); para = para[90:]; y -= 12
                    if y < 80: draw_footer(page_num); c.showPage(); page_num += 1; y = height - 90
                c.drawString(46, y, para); y -= 12
                if y < 80: draw_footer(page_num); c.showPage(); page_num += 1; y = height - 90

        # draw small charts if available (we assume images were generated and paths given)
        chart_path = obj.get("chart_png")
        if chart_path and os.path.exists(chart_path):
            if y < 320:
                draw_footer(page_num); c.showPage(); page_num += 1; y = height - 90
            safe_draw_image(chart_path, 40, y - 280, 520, 260)
            y -= 300

        draw_footer(page_num)
        c.showPage()
        page_num += 1

    # --- Annex (raw tables) ---
    c.setFont(title_font, 13); c.drawString(40, height - 60, "Annex — Raw tables")
    y = height - 90; c.setFont("Helvetica", 9)
    for key, obj in indicator_data.items():
        yearly = obj.get("yearly")
        if yearly is None:
            continue
        c.drawString(40, y, f"{key.capitalize()} — Yearly table"); y -= 12
        for _, r in yearly.iterrows():
            try:
                c.drawString(46, y, f"{int(r['Year'])} | {r['total_value']:,.2f}")
            except Exception:
                pass
            y -= 10
            if y < 60:
                draw_footer(page_num); c.showPage(); page_num += 1; y = height - 90
        y -= 8

    draw_footer(page_num)
    c.save()
    buf.seek(0)
    return buf
