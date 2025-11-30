import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from src.ai_agent.agent import SustainabilityAgentPro
from src.ai_agent.kpi_service import compute_yearly_totals, forecast_next_year
from src.ai_agent.reporting import build_indicator_narrative


# ----------------------------------------
# PAGE CONFIG
# ----------------------------------------
st.set_page_config(page_title="GRI PDF Report", layout="wide")
st.title("📄 GRI Sustainability Report Generator")


# ----------------------------------------
# INIT AGENT
# ----------------------------------------
if "agent" not in st.session_state:
    st.session_state.agent = SustainabilityAgentPro()

agent = st.session_state.agent

OUT_DIR = "output"
os.makedirs(OUT_DIR, exist_ok=True)


# ----------------------------------------
# SIDEBAR SETTINGS
# ----------------------------------------
with st.sidebar:
    st.header("Report Settings")

    indicator = st.selectbox("Indicator", ["energy", "water", "emissions", "waste"])
    years_input = st.text_input("Years (e.g. 2018,2019 or 2017-2021)", value="")

    include_monthly = st.checkbox("Include Monthly Section", value=True)
    include_forecast = st.checkbox("Include Forecast Section", value=True)
    include_anomalies = st.checkbox("Include Anomalies Section", value=True)
    include_narrative = st.checkbox("Include Automated GRI Narratives", value=True)

    logo_path = st.text_input("Logo Path (optional)", value="assets/logo.png")


# ----------------------------------------
# PARSE YEARS
# ----------------------------------------
def parse_years(text, all_years):
    text = text.strip()
    if not text:
        return all_years

    try:
        if "-" in text:
            a, b = text.split("-")
            return list(range(int(a.strip()), int(b.strip()) + 1))

        return [int(x.strip()) for x in text.split(",")]
    except:
        st.warning("Failed to parse years — using all available years.")
        return all_years


# ----------------------------------------
# LOAD DATA
# ----------------------------------------
try:
    df = agent._get_data(indicator)
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

try:
    yearly = compute_yearly_totals(df)
except:
    yearly = df.groupby("Year").agg(total_value=("Value", "sum")).reset_index()

available_years = sorted(yearly["Year"].unique())
selected_years = parse_years(years_input, available_years)

yearly_sel = yearly[yearly["Year"].isin(selected_years)]
if yearly_sel.empty:
    yearly_sel = yearly.copy()
    selected_years = available_years

unit_label = df["Unit"].iloc[0] if "Unit" in df.columns else "unit"

st.markdown(f"**Unit:** {unit_label} — **Years Included:** {selected_years}")


# ----------------------------------------
# PLOTTING HELPERS
# ----------------------------------------
def plot_trend(yearly_df, indicator_key, path):
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(yearly_df["Year"], yearly_df["total_value"], marker="o", linewidth=2)
    ax.set_title(f"{indicator_key.upper()} — Yearly Trend")
    ax.set_xlabel("Year")
    ax.set_ylabel(unit_label)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_monthly(df_all, year, indicator_key, path):
    df_y = df_all[df_all["Year"] == year].copy()
    if "Month" not in df_y.columns:
        return None

    df_m = df_y.groupby("Month").agg(Value=("Value", "sum")).reset_index()

    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(df_m["Month"], df_m["Value"], alpha=0.6)
    ax.plot(df_m["Month"], df_m["Value"], marker="o")
    ax.set_xticks(range(1, 13))
    ax.set_title(f"{indicator_key.upper()} — Monthly {year}")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ----------------------------------------
# FORECAST HELPER
# ----------------------------------------
def try_forecast(data):
    try:
        return forecast_next_year(data)
    except:
        return None, None


# ----------------------------------------
# ANOMALY DETECTOR
# ----------------------------------------
def detect_anomalies(series, threshold=3.0):
    s = series.dropna()
    mu, sigma = s.mean(), s.std(ddof=0)
    if sigma == 0:
        return pd.Series([False] * len(series))
    z = (series - mu) / sigma
    return z.abs() > threshold


# ----------------------------------------
# PDF GENERATOR
# ----------------------------------------
def build_pdf(indicator_key, yearly_df, df_all, out_path):

    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4

    # COVER PAGE
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height-60, f"GRI Report — {indicator_key.upper()}")

    if os.path.exists(logo_path):
        c.drawImage(logo_path, width-140, height-140, width=100, height=100)

    c.showPage()

    # PLOTS
    trend_img = f"{OUT_DIR}/{indicator_key}_trend.png"
    plot_trend(yearly_df, indicator_key, trend_img)

    if include_monthly:
        y_latest = yearly_df["Year"].max()
        monthly_img = f"{OUT_DIR}/{indicator_key}_monthly.png"
        plot_monthly(df_all, y_latest, indicator_key, monthly_img)

    # TREND PAGE
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height-60, "Yearly Trend")
    if os.path.exists(trend_img):
        c.drawImage(trend_img, 40, height-420, width=520, height=300)
    c.showPage()

    # MONTHLY PAGE
    if include_monthly and os.path.exists(monthly_img):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height-60, "Monthly Analysis")
        c.drawImage(monthly_img, 40, height-420, width=520, height=300)
        c.showPage()

    # FORECAST PAGE
    if include_forecast:
        fy, fv = try_forecast(yearly_df)
        if fy and fv:
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, height-60, "Forecast")
            c.setFont("Helvetica", 12)
            c.drawString(40, height-90, f"Forecast Year: {fy}")
            c.drawString(40, height-110, f"Predicted Value: {fv:,.2f}")
            c.showPage()

    # ANOMALIES PAGE
    if include_anomalies:
        yearly_df = yearly_df.copy()
        yearly_df["anomaly"] = detect_anomalies(yearly_df["total_value"])

        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height-60, "Anomalies")
        ypos = height-100
        for _, r in yearly_df[yearly_df["anomaly"]].iterrows():
            c.drawString(40, ypos, f"{int(r['Year'])} — {r['total_value']:,.2f}")
            ypos -= 18
            if ypos < 60:
                c.showPage()
                ypos = height-100
        c.showPage()

    # NARRATIVE PAGE
    if include_narrative:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height-60, "GRI Narrative")
        ypos = height-100

        for y in yearly_df["Year"]:
            text = build_indicator_narrative(indicator_key, df_all, int(y), unit_label)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, ypos, f"{y}:")
            ypos -= 16

            c.setFont("Helvetica", 10)
            for line in text.split("\n"):
                c.drawString(60, ypos, line[:100])
                ypos -= 14
                if ypos < 60:
                    c.showPage()
                    ypos = height-100
        c.showPage()

    c.save()
    return out_path


# ----------------------------------------
# GENERATE PDF BUTTON
# ----------------------------------------
st.write("---")
if st.button("Generate GRI PDF"):
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    pdf_name = f"{indicator}_GRI_Report_{now}.pdf"
    pdf_path = os.path.join(OUT_DIR, pdf_name)

    try:
        build_pdf(indicator, yearly_sel, df, pdf_path)
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download PDF", f, file_name=pdf_name)
        st.success("PDF generated successfully!")
    except Exception as e:
        st.error(f"Failed to build PDF: {e}")
