import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from src.ai_agent.agent import SustainabilityAgentPro
from src.ai_agent.kpi_service import compute_yearly_totals, forecast_next_year
from src.ai_agent.reporting import build_indicator_narrative
from src.email_sender import send_pdf_via_email

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="GRI PDF Report Generator", layout="wide")
st.title("📄 GRI-style Report Generator — EGY-WOOD")

# ensure output folder
OUT_DIR = "output"
os.makedirs(OUT_DIR, exist_ok=True)

# Agent init
if "agent" not in st.session_state:
    st.session_state.agent = SustainabilityAgentPro()
agent = st.session_state.agent

# Sidebar controls
with st.sidebar:
    st.header("Report Settings")
    indicator = st.selectbox("Select Indicator", ["energy", "water", "emissions", "waste"])
    years_text = st.text_input("Years (comma-separated or range)", value="")
    include_monthly = st.checkbox("Include monthly section", value=True)
    include_forecast = st.checkbox("Include forecast section", value=True)
    include_anomalies = st.checkbox("Include anomalies table", value=True)
    include_narrative = st.checkbox("Include GRI narrative (automated)", value=True)
    logo_path = st.text_input("Company Logo", value="assets/company_logo.png")

st.write(f"**Selected Indicator:** {indicator}")

# --- Parse years ---
def parse_years(text, all_years):
    text = text.strip()
    if not text:
        return sorted(all_years)
    try:
        if "-" in text:
            a, b = text.split("-")
            return list(range(int(a), int(b) + 1))
        return [int(x) for x in text.split(",") if x.strip()]
    except:
        st.warning("Invalid year format — using all available years.")
        return sorted(all_years)

# --- Load data ---
try:
    df = agent._get_data(indicator)
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

# Compute yearly totals
try:
    yearly = compute_yearly_totals(df)
except:
    yearly = df.groupby("Year").agg(total_value=("Value", "sum")).reset_index()

available_years = sorted(yearly["Year"].unique())
selected_years = parse_years(years_text, available_years)

yearly_sel = yearly[yearly["Year"].isin(selected_years)]
if yearly_sel.empty:
    yearly_sel = yearly.copy()
    selected_years = available_years

unit_label = df["Unit"].iloc[0] if "Unit" in df.columns else ""

# ---------------------------
# Plot Helpers
# ---------------------------
def plot_trend(yearly_df, indicator_label, out_path):
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(yearly_df["Year"], yearly_df["total_value"], marker="o")
    ax.set_title(f"{indicator_label} — Yearly Trend")
    ax.set_xlabel("Year")
    ax.set_ylabel(unit_label)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

def plot_monthly(df_all, year, indicator_label, out_path):
    df_y = df_all[df_all["Year"] == year]
    if "Month" not in df_y.columns:
        return None
    df_mon = df_y.groupby("Month").agg(Value=("Value", "sum")).reset_index()
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.bar(df_mon["Month"], df_mon["Value"])
    ax.plot(df_mon["Month"], df_mon["Value"], marker="o")
    ax.set_title(f"{indicator_label} — Monthly {year}")
    ax.set_xlabel("Month")
    ax.set_ylabel(unit_label)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path

# ---------------------------
# PDF GENERATOR
# ---------------------------
def build_pdf(indicator_key, yearly_df, df_all, out_pdf):

    indicator_label = indicator_key.upper()
    trend_img = os.path.join(OUT_DIR, f"{indicator_key}_trend.png")
    plot_trend(yearly_df, indicator_label, trend_img)

    monthly_img = None
    if include_monthly:
        y = yearly_df["Year"].max()
        monthly_img = os.path.join(OUT_DIR, f"{indicator_key}_monthly_{y}.png")
        plot_monthly(df_all, y, indicator_label, monthly_img)

    # Forecast
    fy, fv = forecast_next_year(yearly_df) if include_forecast else (None, None)

    # Detect anomalies
    yearly_df = yearly_df.copy()
    yearly_df["anomaly"] = (yearly_df["total_value"] - yearly_df["total_value"].mean()).abs() > 3 * yearly_df["total_value"].std()

    # Narrative
    narratives = {}
    if include_narrative:
        for y in yearly_df["Year"]:
            try:
                narratives[y] = build_indicator_narrative(indicator_key, df_all, int(y), unit_label)
            except:
                narratives[y] = "(No narrative available)"

    # Start PDF
    c = canvas.Canvas(out_pdf, pagesize=A4)
    w, h = A4

    # --- Cover Page ---
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(w/2, h-60, f"EGY-WOOD — GRI Report")
    c.setFont("Helvetica", 14)
    c.drawCentredString(w/2, h-85, f"Indicator: {indicator_label}")
    c.drawCentredString(w/2, h-105, f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    # Logo
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, w-150, h-160, width=100, height=100)
        except:
            pass

    c.showPage()

    # --- Trend ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h-60, "Yearly Trend")
    c.drawImage(trend_img, 40, h-420, width=520, height=300)
    c.showPage()

    # --- Monthly ---
    if include_monthly and monthly_img and os.path.exists(monthly_img):
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, h-60, "Monthly Breakdown")
        c.drawImage(monthly_img, 40, h-420, width=520, height=300)
        c.showPage()

    # --- Forecast ---
    if fy and fv:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, h-60, "Forecast")
        c.setFont("Helvetica", 12)
        c.drawString(40, h-90, f"Forecast Year: {fy}")
        c.drawString(40, h-110, f"Expected Value: {fv:.2f} {unit_label}")
        c.showPage()

    # --- Anomalies ---
    if include_anomalies:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, h-60, "Anomalies Detected")
        c.setFont("Helvetica", 12)
        y = h-100
        for _, row in yearly_df.iterrows():
            if row["anomaly"]:
                c.drawString(40, y, f"{int(row['Year'])}: {row['total_value']:.2f} {unit_label}")
                y -= 20
        c.showPage()

    # --- GRI Narrative ---
    if include_narrative:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, h-60, "GRI Alignment Narrative")
        c.setFont("Helvetica", 10)
        y = h-90

        for year, text in narratives.items():
            c.drawString(40, y, f"{year}:")
            y -= 15
            for line in text.split("\n"):
                c.drawString(60, y, line[:120])
                y -= 12
                if y < 50:
                    c.showPage()
                    y = h-90
        c.showPage()

    c.save()
    return out_pdf

# ---------------------------
# Generate PDF
# ---------------------------
st.write("---")
st.subheader("Build Full Report")

if st.button("Generate Full GRI PDF"):
    now = datetime.utcnow().strftime("%Y%m%d_%H%M")
    pdf_name = f"EGY-WOOD_GRI_Report_{now}.pdf"
    pdf_path = os.path.join(OUT_DIR, pdf_name)

    try:
        build_pdf(indicator, yearly_sel, df, pdf_path)
        st.success("PDF generated successfully!")
    except Exception as e:
        st.error(f"PDF generation failed: {e}")
        st.stop()

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    st.download_button("📥 Download Report", pdf_bytes, file_name=pdf_name)

    # ----------------------------
    # EMAIL SEND SECTION (FIXED)
    # ----------------------------
    st.subheader("📧 Send Report via Email")
    receiver = st.text_input("Recipient email(s) — comma separated")

    if st.button("Send Email"):
        emails = [e.strip() for e in receiver.split(",") if e.strip()]

        for em in emails:
            try:
                send_pdf_via_email(
                    receiver_email=em,
                    pdf_bytes=pdf_bytes,
                    pdf_name=pdf_name,
                    year=datetime.utcnow().year
                )
                st.success(f"Sent successfully → {em}")
            except Exception as e:
                st.error(f"Email failed for {em}: {e}")
