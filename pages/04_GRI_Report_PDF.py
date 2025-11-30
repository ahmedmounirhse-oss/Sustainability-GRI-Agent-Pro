from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from datetime import datetime
import os

def build_pdf(indicator_key, yearly_df, df_all, out_pdf):

    indicator_label = indicator_key.upper()
    trend_img = os.path.join(OUT_DIR, f"{indicator_key}_trend.png")
    monthly_img = os.path.join(OUT_DIR, f"{indicator_key}_monthly.png")

    # Create canvas
    c = canvas.Canvas(out_pdf, pagesize=A4)
    w, h = A4

    # ----------------------------
    # COVER PAGE — GREEN THEME
    # ----------------------------
    c.setFillColor("#2E7D32")
    c.rect(0, 0, w, h, fill=1)

    c.setFillColor("white")
    c.setFont("Helvetica-Bold", 34)
    c.drawString(40, h - 120, "EGY-WOOD")
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, h - 160, "GRI Sustainability Report")

    c.setFont("Helvetica", 16)
    c.drawString(40, h - 200, f"Indicator: {indicator_label}")
    c.drawString(40, h - 230, f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    # Logo
    if os.path.exists(logo_path):
        c.drawImage(logo_path, w - 180, h - 180, width=110, height=110)

    c.showPage()

    # ----------------------------
    # KPI SUMMARY TABLE
    # ----------------------------
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor("#2E7D32")
    c.drawString(40, h - 50, "KPI Summary")

    data = [["Year", "Total Value", "Δ % YoY", "Unit"]]

    prev_value = None
    for _, row in yearly_df.iterrows():
        year = int(row["Year"])
        val = row["total_value"]
        unit = df_all["Unit"].iloc[0] if "Unit" in df_all.columns else ""

        if prev_value is None:
            change = "—"
        else:
            change = f"{((val - prev_value) / prev_value) * 100:.1f}%"
        prev_value = val

        data.append([str(year), f"{val:,.2f}", change, unit])

    table = Table(data, colWidths=[4*cm, 5*cm, 4*cm, 3*cm])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#A5D6A7")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 12),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#F5F5F5")),
    ]))

    table.wrapOn(c, w, h)
    table.drawOn(c, 40, h - 300)

    c.showPage()

    # ----------------------------
    # TREND CHART PAGE
    # ----------------------------
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor("#2E7D32")
    c.drawString(40, h - 50, "Yearly Trend Chart")

    if os.path.exists(trend_img):
        c.drawImage(trend_img, 40, h - 450, width=500, height=350)

    c.showPage()

    # ----------------------------
    # MONTHLY CHART
    # ----------------------------
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor("#2E7D32")
    c.drawString(40, h - 50, "Monthly Breakdown")

    if os.path.exists(monthly_img):
        c.drawImage(monthly_img, 40, h - 450, width=500, height=350)

    c.showPage()

    # ----------------------------
    # FORECAST SECTION
    # ----------------------------
    fy, fv = forecast_next_year(yearly_df)

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor("#2E7D32")
    c.drawString(40, h - 50, "Next Year Forecast")

    c.setFont("Helvetica", 14)
    c.setFillColor("black")
    c.drawString(40, h - 100, f"Forecast Year: {fy}")
    c.drawString(40, h - 130, f"Expected Value: {fv:,.2f}")

    c.showPage()

    # ----------------------------
    # ANOMALIES
    # ----------------------------
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor("#2E7D32")
    c.drawString(40, h - 50, "Anomalies Detected")

    yearly_df["anomaly"] = (yearly_df["total_value"] - yearly_df["total_value"].mean()).abs() > 3 * yearly_df["total_value"].std()

    y = h - 120
    c.setFont("Helvetica", 13)
    for _, row in yearly_df.iterrows():
        if row["anomaly"]:
            c.drawString(40, y, f"{int(row['Year'])} — {row['total_value']:,.2f}")
            y -= 25

    c.showPage()

    # ----------------------------
    # NARRATIVE PAGE
    # ----------------------------
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor("#2E7D32")
    c.drawString(40, h - 50, "GRI Narrative")

    style = ParagraphStyle(
        name="Narrative",
        fontName="Helvetica",
        fontSize=12,
        leading=16
    )

    narratives = []
    for _, row in yearly_df.iterrows():
        year = int(row["Year"])
        try:
            text = build_indicator_narrative(indicator_key, df_all, year, "")
        except:
            text = "(Narrative not available)"

        narratives.append(f"<b>{year}</b><br/>{text}<br/><br/>")

    story = [Paragraph(n, style) for n in narratives]

    y_position = h - 130
    for p in story:
        w_, h_ = p.wrap(500, y_position)
        if y_position - h_ < 50:
            c.showPage()
            y_position = h - 130
        p.drawOn(c, 40, y_position - h_)
        y_position -= (h_ + 20)

    c.showPage()

    # ----------------------------
    # FOOTER
    # ----------------------------
    c.setFillColor("#2E7D32")
    c.rect(0, 0, w, 70, fill=1)

    c.setFillColor("white")
    c.setFont("Helvetica", 12)
    c.drawString(40, 30, "EGY-WOOD Sustainability Reporting Team — GRI Standards")
    c.drawString(40, 15, "Contact: sustainability@egywood.com")

    c.save()

    return out_pdf
