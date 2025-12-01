# pages/02_KPI_Dashboard.py

import os
import time
from pathlib import Path
from itertools import cycle

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Project imports
from src.ai_agent.agent import SustainabilityAgentPro
from src.ai_agent.kpi_service import compute_yearly_totals, forecast_next_year

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("📊 KPI Dashboard — Sustainability Metrics")

DATA_DIR = Path("data")
OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)

# ============================================================
#                AUTO-LIVE-RELOAD ENGINE (FINAL)
# ============================================================

if "last_snapshot" not in st.session_state:
    st.session_state.last_snapshot = {}
if "last_check" not in st.session_state:
    st.session_state.last_check = 0

def get_snapshot():
    snap = {}
    for f in DATA_DIR.glob("*.xlsx"):
        try:
            snap[str(f)] = os.path.getmtime(f)
        except:
            pass
    return snap

def snapshot_changed(old, new):
    if old.keys() != new.keys():
        return True
    for f, ts in new.items():
        if f not in old or old[f] != ts:
            return True
    return False

now = time.time()
if now - st.session_state.last_check > 3:
    st.session_state.last_check = now

    new = get_snapshot()
    if snapshot_changed(st.session_state.last_snapshot, new):
        st.session_state.last_snapshot = new

        if "agent" in st.session_state:
            st.session_state.agent._cache = {}

        st.toast("🔄 Data updated — refreshing dashboard...", icon="🔥")

        try:
            st.rerun()
        except:
            pass

# -------------------------
# Init agent
# -------------------------
if "agent" not in st.session_state:
    st.session_state.agent = SustainabilityAgentPro()
agent: SustainabilityAgentPro = st.session_state.agent

# ============================================================
#                  SIDEBAR CONTROLS
# ============================================================

with st.sidebar:
    st.header("⚙️ Controls")
    primary_indicator = st.selectbox("Primary Indicator", ["energy", "water", "emissions", "waste"])
    anomaly_threshold = st.number_input("Anomaly threshold (z-score)", value=3.0, min_value=1.0, max_value=6.0)

    st.write("📂 Files detected:")
    files_here = [f.name for f in DATA_DIR.glob("*.xlsx")]
    if files_here:
        for f in files_here:
            st.write("📄", f)
    else:
        st.warning("⚠️ No Excel files found in /data")

# ============================================================
#                LOAD INDICATOR DATA
# ============================================================

try:
    df = agent._get_data(primary_indicator)
except Exception as e:
    st.error(f"Failed to load data for '{primary_indicator}': {e}")
    st.stop()

if "Year" not in df.columns or "Value" not in df.columns:
    st.error("Data missing required columns: Year, Value")
    st.stop()

# Yearly summary
try:
    yearly = compute_yearly_totals(df)
except:
    yearly = df.groupby("Year", as_index=False).agg(total_value=("Value", "sum"))

yearly = yearly.sort_values("Year").reset_index(drop=True)

# Detect anomalies
def detect_anomalies(series, threshold):
    if series.std() == 0:
        return pd.Series(False, index=series.index)
    z = (series - series.mean()) / series.std()
    return z.abs() > threshold

yearly["anomaly"] = detect_anomalies(yearly["total_value"], anomaly_threshold)

# ============================================================
#                MAIN CONTROLS
# ============================================================

years_available = sorted(yearly["Year"].unique())
year_min, year_max = years_available[0], years_available[-1]

yr1, yr2 = st.slider(
    "Select Year Range",
    min_value=int(year_min),
    max_value=int(year_max),
    value=(int(year_min), int(year_max))
)

filtered = yearly[(yearly["Year"]>=yr1) & (yearly["Year"]<=yr2)]

# ============================================================
#                TABS LAYOUT
# ============================================================

tab_trend, tab_summary, tab_download, tab_monthly, tab_forecast, tab_compare = st.tabs(
    ["📈 Trend", "📘 Summary", "⬇️ Downloads", "📅 Monthly", "📉 Forecast", "📊 Comparison"]
)

# -------------------------
# TAB: Trend
# -------------------------
with tab_trend:
    st.subheader(f"📈 {primary_indicator.upper()} Trend")

    fig, ax = plt.subplots(figsize=(10,4))
    ax.plot(filtered["Year"], filtered["total_value"], marker="o", linewidth=2)

    # anomalies red highlight
    anomalies = filtered[filtered["anomaly"]]
    ax.scatter(anomalies["Year"], anomalies["total_value"], color="red", s=60)

    ax.set_xlabel("Year")
    ax.set_ylabel(df["Unit"].iloc[0])
    ax.grid(alpha=0.2)
    st.pyplot(fig)

# -------------------------
# TAB: Summary
# -------------------------
with tab_summary:
    st.subheader("📘 Summary")

    st.dataframe(filtered, use_container_width=True)

# -------------------------
# TAB: Downloads
# -------------------------
with tab_download:
    st.subheader("⬇️ Downloads")
    csv_bytes = filtered.to_csv(index=False).encode()
    st.download_button("Download CSV", csv_bytes, file_name=f"{primary_indicator}_filtered.csv")

# -------------------------
# TAB: Monthly
# -------------------------
with tab_monthly:
    st.subheader("📅 Monthly Analysis")

    if "Month" not in df.columns:
        st.warning("No monthly data found in dataset.")
    else:
        sel_year = st.selectbox("Select Year", years_available)
        mdf = df[df["Year"] == sel_year].sort_values("Month")

        fig2, ax2 = plt.subplots(figsize=(10,4))
        ax2.bar(mdf["Month"], mdf["Value"], alpha=0.5)
        ax2.plot(mdf["Month"], mdf["Value"], marker="o")

        st.pyplot(fig2)
        st.dataframe(mdf, use_container_width=True)

# -------------------------
# TAB: Forecast
# -------------------------
with tab_forecast:
    st.subheader("📉 Forecast")

    try:
        nxt, pred = forecast_next_year(yearly)
        st.metric(f"Forecast {nxt}", f"{pred:,.2f} {df['Unit'].iloc[0]}")
    except:
        st.warning("Forecast unavailable")

# -------------------------
# TAB: Comparison
# -------------------------
with tab_compare:
    st.subheader("📊 Compare Indicators")

    inds = st.multiselect("Choose indicators", ["energy","water","emissions","waste"], default=["energy","water"])

    if len(inds) >= 2:
        combined = pd.DataFrame()
        for ind in inds:
            dfi = agent._get_data(ind)
            ydf = compute_yearly_totals(dfi)
            combined[ind] = ydf.set_index("Year")["total_value"]
        st.line_chart(combined)
