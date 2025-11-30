# src/report_generator.py
import os
import io
from datetime import datetime
from typing import List, Optional, Dict

import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from src.ai_agent.agent import SustainabilityAgentPro
from src.ai_agent.kpi_service import compute_yearly_totals, forecast_next_year
from src.ai_agent.reporting import build_indicator_narrative

AGENT = None

def get_agent():
    global AGENT
    if AGENT is None:
        AGENT = SustainabilityAgentPro()
    return AGENT

def _plot_to_bytes(fig):
    bio = io.BytesIO()
    fig.savefig(bio, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    bio.seek(0)
    return bio

def _make_trend_plot(yearly_df: pd.DataFrame, unit: str, title: str):
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(yearly_df["Year"], yearly_df["total_value"], marker="o", linewidth=2)
    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel(unit)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return _plot_to_bytes(fig)

def _make_monthly_plot(df: pd.DataFrame, year: int, unit: str, title: str):
    dfy = df[df["Year"] == year].copy()
    if "Month" not in dfy.columns or dfy.empty:
        return None
    dfm = dfy.groupby("Month", as_index=False).agg(Value=("Value", "sum"))
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.bar(dfm["Month"], dfm["Value"], alpha=0.6)
    ax.plot(dfm["Month"], dfm["Value"], marker="o")
    ax.set_xticks(range(1, 13))
    ax.set_xlabel("Month")
    ax.set_ylabel(unit)
    ax.set_title(title)
    fig.tight_layout()
    return _plot_to_bytes(fig)

def _compute_intensity(total_value: float, basis_value: float) -> Optional[float]:
    try:
        return total_value / basis_value
    except Exception:
        return None

def build_gri_pdf_report(
    year: int,
    indicators: List[str] = ["energy", "water", "emissions", "waste"],
    include_monthly: bool = True,
    include_forecast: bool = True,
    include_anomalies: bool = True,
    basis_for_intensity: Dict[str, float] = None,
    logo_path: Optional[str] = None,
) -> io.BytesIO:
    """
    Build a multi-indicator GRI-style PDF for a given year.
    Returns: BytesIO (PDF bytes)
    basis_for_intensity: optional dict mapping indicator -> basis value (e.g., production ton)
    """
    agent = get_agent()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Cover page
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(w/2, h-80, f"GRI Sustainability Report — {year}")
    c.setFont("Helvetica", 10)
    c.drawCentredString(w/2, h-100, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, w-140, h-160, width=100, height=100, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    c.showPage()

    # For each indicator create sections
    for ind in indicators:
        try:
            df = agent._get_data(ind)
        except Exception as e:
            # skip missing indicator but add note
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, h-80, f"{ind.upper()} — Data not found")
            c.setFont("Helvetica", 10)
            c.drawString(40, h-100, str(e))
            c.showPage()
            continue

        unit = df["Unit"].iloc[0] if "Unit" in df.columns else ""
        yearly = compute_yearly_totals(df)
        # pick the requested year if present
        row = yearly[yearly["Year"] == int(year)]
        if row.empty:
            total_value = 0.0
        else:
            total_value = float(row["total_value"].iloc[0])

        # KPI Summary
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, h-80, f"{ind.upper()} — KPI Summary ({year})")
        c.setFont("Helvetica", 11)
        ypos = h-110
        c.drawString(40, ypos, f"Total: {total_value:,.2f} {unit}")
        ypos -= 16

        # intensity (if basis provided)
        if basis_for_intensity and ind in basis_for_intensity:
            intensity = _compute_intensity(total_value, basis_for_intensity[ind])
            c.drawString(40, ypos, f"Intensity (per basis): {intensity:,.4f} (basis={basis_for_intensity[ind]})")
            ypos -= 16

        # anomaly check (simple z)
        if include_anomalies:
            mu = yearly["total_value"].mean()
            sigma = yearly["total_value"].std(ddof=0)
            is_anom = False
            if sigma and sigma != 0:
                z = (total_value - mu) / sigma
                is_anom = abs(z) > 3.0
            c.drawString(40, ypos, f"Anomaly (z>3): {'Yes' if is_anom else 'No'}")
            ypos -= 16

        # narrative
        try:
            narrative = build_indicator_narrative(ind, df, int(year), unit_label=unit)
            if narrative:
                c.drawString(40, ypos, "Narrative:")
                ypos -= 14
                # write a few lines wrapping
                for para in str(narrative).split("\n"):
                    # split by ~100 chars
                    while len(para) > 100:
                        c.drawString(60, ypos, para[:100])
                        para = para[100:]
                        ypos -= 12
                    c.drawString(60, ypos, para)
                    ypos -= 12
        except Exception:
            pass

        c.showPage()

        # Trend plot (image bytes)
        try:
            plot_bytes = _make_trend_plot(yearly, unit, f"{ind.upper()} — Trend")
            if plot_bytes:
                # draw image
                c.drawImage(plot_bytes, 40, h-420, width=520, height=300)
                c.showPage()
        except Exception:
            pass

        # Monthly plot
        if include_monthly:
            try:
                monthly_img = _make_monthly_plot(df, int(year), unit, f"{ind.upper()} — Monthly {year}")
                if monthly_img:
                    c.drawImage(monthly_img, 40, h-420, width=520, height=300)
                    c.showPage()
            except Exception:
                pass

        # Forecast
        if include_forecast:
            try:
                # use latest window from yearly
                fy, fv = forecast_next_year(yearly)
                if fy and fv:
                    c.setFont("Helvetica-Bold", 14)
                    c.drawString(40, h-80, "Forecast")
                    c.setFont("Helvetica", 11)
                    c.drawString(40, h-100, f"Next year: {fy} — Predicted: {fv:,.2f} {unit}")
                    c.showPage()
            except Exception:
                pass

    # finalize
    c.save()
    buf.seek(0)
    return buf
