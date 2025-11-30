# pages/04_GRI_Report_PDF.py
import os
import io
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -------------------------
# Attempt to import shared helpers (if you created them)
# -------------------------
try:
    from src.report_generator import build_gri_pdf_report  # preferred: externalized function
    has_remote_builder = True
except Exception:
    has_remote_builder = False

# If remote builder not available, provide a fallback implementation (self-contained)
if not has_remote_builder:
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
        Fallback PDF builder — returns BytesIO with PDF content.
        indicator_data: {
            "energy": {"yearly": DataFrame, "monthly": DataFrame or None, "narrative": str, "chart_png": path or None, "forecast": (yr,val) or None},
            ...
        }
        """
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4

        def draw_footer(page_num: int):
            footer_y = 12 * mm
            c.setFont("Helvetica", 8)
            c.setFillGray(0.45)
            c.drawCentredString(width / 2, footer_y, f"{project_name} — GRI Report  •  Page {page_num}")

        def safe_draw_image(img_path, x, y, w, h):
            try:
                if img_path and os.path.exists(img_path):
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
        for key, obj in indicator_data.items():
            yearly = obj.get("yearly")
            latest_text = "data not available"
            try:
                latest = yearly.sort_values("Year").iloc[-1]
                val = latest["total_value"]
                latest_text = f"{val:,.2f} {unit_label}"
            except Exception:
                pass
            c.drawString(50, y, f"- {key.capitalize()}: latest {latest_text}")
            y -= 12
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

            narrative = obj.get("narrative")
            if narrative:
                if y < 170:
                    draw_footer(page_num); c.showPage(); page_num += 1; y = height - 90
                c.setFont("Helvetica-Bold", 11); c.drawString(40, y, "Narrative"); y -= 16
                c.setFont("Helvetica", 10)
                for para in str(narrative).split("\n"):
                    while len(para) > 90:
                        chunk = para[:90]; c.drawString(46, y, chunk); para = para[90:]; y -= 12
                        if y < 80: draw_footer(page_num); c.showPage(); page_num += 1; y = height - 90
                    c.drawString(46, y, para); y -= 12
                    if y < 80: draw_footer(page_num); c.showPage(); page_num += 1; y = height - 90

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

# -------------------------
# Page UI
# -------------------------
st.set_page_config(page_title="GRI PDF Report Generator", layout="wide")
st.title("📄 GRI PDF Report Generator — EGY-WOOD")

# Ensure output folder exists
OUT_DIR = Path("output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load the unified agent (SustainabilityAgentPro)
try:
    from src.ai_agent.agent import SustainabilityAgentPro
    from src.ai_agent.kpi_service import compute_yearly_totals, forecast_next_year
    from src.ai_agent.reporting import build_indicator_narrative
except Exception as e:
    st.error(f"Failed to import agent or services: {e}")
    st.stop()

# Instantiate agent (singleton per session)
if "agent" not in st.session_state:
    st.session_state.agent = SustainabilityAgentPro()
agent = st.session_state.agent

# Sidebar: settings
with st.sidebar:
    st.header("Report settings")
    indicators_choices = ["energy", "water", "emissions", "waste"]
    selected_indicators = st.multiselect("Indicators to include", indicators_choices, default=indicators_choices)
    include_monthly = st.checkbox("Include monthly section", value=True)
    include_forecast = st.checkbox("Include forecast section", value=True)
    include_anomalies = st.checkbox("Include anomalies", value=True)
    include_narrative = st.checkbox("Include GRI narrative", value=True)
    logo_path = st.text_input("Logo path (relative)", value="assets/company_logo.png")
    unit_override = st.text_input("Unit label (optional)", value="")  # if blank, taken from data

st.write("Selected indicators:", ", ".join(selected_indicators))

# Build indicator_data
indicator_data = {}
unit_label_global = None

for key in selected_indicators:
    try:
        df = agent._get_data(key)
    except Exception as e:
        st.warning(f"Could not load data for {key}: {e}")
        continue

    # compute yearly totals
    try:
        yearly = compute_yearly_totals(df)
    except Exception:
        yearly = df.groupby("Year").agg(total_value=("Value", "sum")).reset_index()
        yearly["change_abs"] = yearly["total_value"].diff()
        yearly["change_pct"] = yearly["total_value"].pct_change() * 100

    # basic anomaly detection (z-score)
    def detect_anomalies_simple(series, threshold=3.0):
        s = series.dropna()
        mu, sigma = s.mean(), s.std(ddof=0)
        if sigma == 0 or pd.isna(sigma):
            return pd.Series([False] * len(series), index=series.index)
        z = (series - mu) / sigma
        return z.abs() > threshold

    yearly = yearly.copy()
    yearly["anomaly"] = detect_anomalies_simple(yearly["total_value"])

    # narrative
    narrative = None
    if include_narrative:
        try:
            latest_year = int(yearly["Year"].max())
            narrative = build_indicator_narrative(key, df, latest_year, unit_label=(df["Unit"].iloc[0] if "Unit" in df.columns else ""))
        except Exception:
            narrative = None

    # generate a small trend chart PNG for embedding
    chart_png = None
    try:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(yearly["Year"], yearly["total_value"], marker="o", linewidth=2)
        anoms = yearly[yearly["anomaly"]]
        if not anoms.empty:
            ax.scatter(anoms["Year"], anoms["total_value"], color="red", s=70, zorder=5)
        ax.set_title(f"{key.capitalize()} — Yearly trend")
        ax.set_xlabel("Year")
        ulabel = df["Unit"].iloc[0] if "Unit" in df.columns else ""
        ax.set_ylabel(ulabel)
        ax.grid(alpha=0.2)
        chart_png = str(OUT_DIR / f"{key}_trend.png")
        fig.tight_layout()
        fig.savefig(chart_png, dpi=150)
        plt.close(fig)
    except Exception:
        chart_png = None

    # forecast (optional)
    forecast = None
    if include_forecast:
        try:
            fy, fv = forecast_next_year(yearly)
            forecast = (fy, fv)
        except Exception:
            forecast = None

    indicator_data[key] = {
        "yearly": yearly,
        "monthly": df[df["Year"] == int(df["Year"].max())] if "Month" in df.columns else None,
        "narrative": narrative,
        "chart_png": chart_png,
        "forecast": forecast,
    }

    # pick a global unit if not overridden
    if not unit_label_global:
        unit_label_global = df["Unit"].iloc[0] if "Unit" in df.columns else ""

# allow manual override
if unit_override.strip():
    unit_label_global = unit_override.strip()

# Build & Download buttons
st.write("---")
st.subheader("Build & download report")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Generate PDF (preview)"):
        if not indicator_data:
            st.error("No indicator data available to build the report.")
        else:
            try:
                buf = build_gri_pdf_report("EGY-WOOD", indicator_data, unit_label=unit_label_global or "")
                st.success("PDF generated — preview ready")
                st.download_button(
                    label="⬇ Download GRI PDF (EGY-WOOD)",
                    data=buf.getvalue(),
                    file_name=f"EGY-WOOD_GRI_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Failed to build PDF: {e}")

with col2:
    st.write("Email options")
    receiver = st.text_input("Recipient email (comma-separated)", value="")
    if st.button("Generate & Send by email"):
        if not indicator_data:
            st.error("No indicator data available to build the report.")
        elif not receiver.strip():
            st.error("Please provide recipient email(s).")
        else:
            try:
                buf = build_gri_pdf_report("EGY-WOOD", indicator_data, unit_label=unit_label_global or "", logo_path=logo_path)
                pdf_bytes = buf.getvalue()

                # Try to use project email sender helper if exists
                try:
                    from src.email_sender import send_pdf_via_email
                    send_pdf_via_email(
                        receiver_emails=[e.strip() for e in receiver.split(",") if e.strip()],
                        pdf_bytes=pdf_bytes,
                        pdf_name=f"EGY-WOOD_GRI_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.pdf"
                    )
                    st.success("Email sent successfully.")
                except Exception as e:
                    # Fallback: save PDF locally and show it for manual sending
                    outfile = OUT_DIR / f"EGY-WOOD_GRI_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.pdf"
                    with open(outfile, "wb") as f:
                        f.write(pdf_bytes)
                    st.warning(f"Automatic email send failed ({e}). PDF saved to {outfile}. You can send manually.")
            except Exception as e:
                st.error(f"Failed to build/send PDF: {e}")

st.write("---")
st.caption("Notes: The report generator uses the latest available year per indicator. Charts are saved temporarily in the `output/` folder and embedded into the PDF if present.")
