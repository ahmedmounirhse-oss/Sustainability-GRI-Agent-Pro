from io import BytesIO
from typing import List, Dict

import pandas as pd
import numpy as np

# ==== IMPORTANT FOR STREAMLIT (Fix blank pages / crashes) ====
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, Image
)

# === FIXED IMPORT PATHS ===
from .config import INDICATORS
from .data_loader import load_indicator
from .kpi_service import compute_yearly_totals, forecast_next_year
from .reporting import build_indicator_narrative


# ========================= STATIC ASSETS ==========================
LOCAL_LOGO_PATH = "assets/company_logo.png"


# ======================== PLOT FUNCTION ===========================
def _plot_yearly_trend(yearly_df, title: str, unit: str) -> BytesIO:
    buf = BytesIO()

    years = yearly_df["Year"].astype(int)
    vals = yearly_df["total_value"]

    plt.figure(figsize=(6, 2.4), dpi=140)
    plt.plot(years, vals, marker="o", linewidth=1.5)
    plt.title(title, fontsize=10)
    plt.ylabel(unit, fontsize=8)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()

    buf.seek(0)
    return buf


# ======================== HELPERS ================================
def _format_num(x):
    try:
        return f"{x:,.2f}"
    except Exception:
        return str(x)


def _build_outlook_text(predicted_value: float, unit: str, next_year: int) -> str:
    return (
        f"The projected performance for <b>{next_year}</b> is estimated at "
        f"<b>{_format_num(predicted_value)} {unit}</b>. "
        f"This outlook reflects historical patterns and expected conditions."
    )


# ========================= MAIN REPORT ============================
def build_gri_pdf_report(year: int) -> BytesIO:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.7 * cm,
        bottomMargin=1.5 * cm,
        title=f"Sustainability GRI Report {year}",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterTitle", parent=styles["Title"], alignment=1))
    styles.add(ParagraphStyle(name="SectionHeader", parent=styles["Heading2"], spaceAfter=10))
    styles.add(ParagraphStyle(name="NormalSmall", parent=styles["Normal"], fontSize=9))

    story = []

    # ===================== COVER PAGE ======================
    try:
        logo = Image(LOCAL_LOGO_PATH, width=6 * cm, height=6 * cm)
        logo.hAlign = "CENTER"
        story.append(logo)
    except Exception:
        pass

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Sustainability GRI Report", styles["CenterTitle"]))
    story.append(Paragraph(f"Reporting Year: <b>{year}</b>", styles["Heading3"]))
    story.append(PageBreak())

    # ================= EXECUTIVE SUMMARY ===================
    story.append(Paragraph("Executive Summary", styles["SectionHeader"]))

    exec_lines = []
    for key, meta in INDICATORS.items():
        df = load_indicator(key)
        yearly = compute_yearly_totals(df)

        row = yearly[yearly["Year"] == year]
        if row.empty:
            exec_lines.append(f"- {meta.kpi_name}: No data for {year}.")
            continue

        r = row.iloc[0]
        total = r["total_value"]
        pct = r["change_pct"]

        if pd.isna(pct):
            trend = "stable performance"
        elif pct > 0:
            trend = f"increased by {pct:.1f}%"
        else:
            trend = f"decreased by {abs(pct):.1f}%"

        exec_lines.append(
            f"- {meta.kpi_name} ({meta.gri_code}): {_format_num(total)} "
            f"{df['Unit'].iloc[0]} ({trend})."
        )

    story.append(Paragraph("<br/>".join(exec_lines), styles["NormalSmall"]))
    story.append(PageBreak())

    # ================== INDICATOR SECTIONS =================
    MONTH_MAP = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    for key, meta in INDICATORS.items():

        df = load_indicator(key)
        yearly = compute_yearly_totals(df)

        row = yearly[yearly["Year"] == year]

        story.append(Paragraph(meta.kpi_name, styles["SectionHeader"]))
        story.append(Paragraph(f"GRI Reference: <b>{meta.gri_code}</b>", styles["Normal"]))
        story.append(Spacer(1, 0.3 * cm))

        if row.empty:
            story.append(Paragraph("No data available.", styles["Normal"]))
            story.append(PageBreak())
            continue

        r = row.iloc[0]
        total = r["total_value"]
        unit = df["Unit"].iloc[0]

        # ===== KPI TABLE =====
        kpi_data = [
            ["Metric", "Value"],
            ["Total", f"{_format_num(total)} {unit}"],
            ["YoY Change", "n/a" if pd.isna(r['change_abs']) else f"{_format_num(r['change_abs'])} {unit}"],
            ["YoY % Change", "n/a" if pd.isna(r['change_pct']) else f"{r['change_pct']:.1f}%"],
        ]

        table = Table(kpi_data, colWidths=[6 * cm, 8 * cm])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ])
        )
        story.append(table)
        story.append(Spacer(1, 0.3 * cm))

        # ===== TREND CHART =====
        chart = _plot_yearly_trend(yearly, meta.kpi_name, unit)
        story.append(Image(chart, width=15 * cm, height=4 * cm))
        story.append(Spacer(1, 0.3 * cm))

        # ===== NARRATIVE =====
        narrative = build_indicator_narrative(key, df, year, unit_label=unit)
        story.append(Paragraph("<b>Narrative</b>", styles["Normal"]))
        story.append(Paragraph(narrative, styles["NormalSmall"]))
        story.append(Spacer(1, 0.4 * cm))

        # ===== OUTLOOK =====
        next_year, prediction = forecast_next_year(yearly)
        outlook = _build_outlook_text(prediction, unit, next_year)

        story.append(Paragraph("<b>Outlook</b>", styles["Normal"]))
        story.append(Paragraph(outlook, styles["NormalSmall"]))
        story.append(Spacer(1, 0.4 * cm))

        # ===== MONTHLY TABLE =====
        monthly = df[df["Year"] == year].copy()
        if not monthly.empty:

            def _conv(m):
                m = str(m).strip().lower()
                return MONTH_MAP.get(m, int(m))

            monthly["Month"] = monthly["Month"].apply(_conv)
            monthly = monthly.sort_values("Month")

            mon_data = [["Month", "Value", "Unit"]]
            for _, row_m in monthly.iterrows():
                mon_data.append([
                    str(row_m["Month"]),
                    _format_num(row_m["Value"]),
                    unit
                ])

            mon_table = Table(mon_data, colWidths=[3 * cm, 4 * cm, 3 * cm])
            mon_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey)
                ])
            )
            story.append(Paragraph("<b>Monthly Data</b>", styles["Normal"]))
            story.append(mon_table)
            story.append(Spacer(1, 0.5 * cm))

        story.append(PageBreak())

    # ===================== APPENDIX =========================
    story.append(Paragraph("Appendix — Annual Raw Data", styles["SectionHeader"]))

    for key, meta in INDICATORS.items():
        df = load_indicator(key)
        yearly = compute_yearly_totals(df)

        story.append(Paragraph(meta.kpi_name, styles["Heading4"]))

        table_data = [["Year", "Total", "Unit"]]
        for _, r in yearly.iterrows():
            table_data.append([
                int(r["Year"]),
                _format_num(r["total_value"]),
                df["Unit"].iloc[0]
            ])

        table = Table(table_data, colWidths=[3 * cm, 5 * cm, 3 * cm])
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))
        story.append(table)
        story.append(Spacer(1, 0.5 * cm))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ================= AVAILABLE YEARS ======================
def get_available_years_for_reports() -> List[int]:
    years = set()
    for key in INDICATORS.keys():
        df = load_indicator(key)
        years.update(df["Year"].unique().tolist())
    return sorted(list(years))
