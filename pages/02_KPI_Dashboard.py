# pages/02_KPI_Dashboard.py
import os
import time
from pathlib import Path
from itertools import cycle

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Project imports (unified agent + helpers)
from src.ai_agent.agent import SustainabilityAgentPro
from src.ai_agent.kpi_service import compute_yearly_totals, forecast_next_year

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("📊 KPI Dashboard — Sustainability Metrics")

# Ensure output folder exists
OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)

# -------------------------
# Initialize (singleton) agent
# -------------------------
if "agent" not in st.session_state:
    st.session_state.agent = SustainabilityAgentPro()

agent: SustainabilityAgentPro = st.session_state.agent

# -------------------------
# DATA AUTO-RELOAD / WATCHER
# -------------------------
DATA_DIR = Path("data")

if "file_timestamps" not in st.session_state:
    st.session_state.file_timestamps = {}

def scan_data_files():
    files = sorted(DATA_DIR.glob("*.xlsx"))
    return files

def detect_file_changes():
    changed = False
    for f in scan_data_files():
        ts = os.path.getmtime(f)
        if f not in st.session_state.file_timestamps:
            st.session_state.file_timestamps[f] = ts
            changed = True
        else:
            if st.session_state.file_timestamps[f] != ts:
                st.session_state.file_timestamps[f] = ts
                changed = True
    # detect deleted files
    known = set(st.session_state.file_timestamps.keys())
    current = set(scan_data_files())
    if known - current:
        for rem in known - current:
            st.session_state.file_timestamps.pop(rem, None)
        changed = True
    return changed

# -------------------------
# Sidebar - global controls
# -------------------------
with st.sidebar:
    st.header("⚙️ Controls")
    primary_indicator = st.selectbox("Primary Indicator", ["energy", "water", "emissions", "waste"], index=0)
    anomaly_threshold = st.number_input("Anomaly z-threshold", value=3.0, min_value=1.0, max_value=6.0, step=0.5)
    enable_autorefresh = st.checkbox("Enable auto-refresh (run every 60s)", value=False)
    refresh_button = st.button("🔄 Refresh Data Now")
    st.markdown("---")
    st.caption("Files in `data/` are scanned automatically. New uploads will trigger a reload when detected.")
    st.write("Data files detected:")
    files_list = [p.name for p in scan_data_files()]
    if files_list:
        for name in files_list:
            st.write(f"- {name}")
    else:
        st.write("No Excel files found in data/")

# Manual refresh action
if refresh_button:
    agent._cache = {}
    st.session_state.file_timestamps = {}
    st.success("Cache cleared — data will reload on demand.")
    st.experimental_rerun()

# Auto-refresh logic
if enable_autorefresh:
    last = st.session_state.get("last_refresh_time", 0)
    now = time.time()
    if now - last > 60:
        st.session_state.last_refresh_time = now
        # re-scan and reload
        if detect_file_changes():
            agent._cache = {}
        st.rerun()

    # still detect file changes once per page load
    if detect_file_changes():
        agent._cache = {}

# -------------------------
# Load primary indicator data
# -------------------------
try:
    df = agent._get_data(primary_indicator)
except Exception as e:
    st.error(f"Failed to load data for indicator '{primary_indicator}': {e}")
    st.stop()

# Basic normalization / expectations
if "Year" not in df.columns or "Value" not in df.columns:
    st.error("Dataframe missing required columns (Year, Value). Check your data files.")
    st.stop()

# Compute yearly totals
try:
    yearly = compute_yearly_totals(df)
except Exception:
    yearly = df.groupby("Year", as_index=False).agg(total_value=("Value", "sum"))
    yearly["change_abs"] = yearly["total_value"].diff()
    yearly["change_pct"] = yearly["total_value"].pct_change() * 100

# Detect anomalies (simple z-score)
def detect_anomalies(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    s = series.dropna()
    mu, sigma = float(s.mean()), float(s.std(ddof=0))
    if sigma == 0 or np.isnan(sigma):
        return pd.Series(False, index=series.index)
    z = (series - mu) / sigma
    return z.abs() > threshold

yearly = yearly.sort_values("Year").reset_index(drop=True)
yearly["anomaly"] = detect_anomalies(yearly["total_value"], anomaly_threshold)

# Year range defaults
years_available = sorted(yearly["Year"].astype(int).unique())
if not years_available:
    st.error("No yearly data available.")
    st.stop()

start_year_default, end_year_default = years_available[0], years_available[-1]

# -------------------------
# Global filters (on page)
# -------------------------
col_controls = st.columns([3, 1, 1])
with col_controls[0]:
    year_range = st.slider("Select year range", min_value=int(start_year_default), max_value=int(end_year_default),
                           value=(int(start_year_default), int(end_year_default)), step=1)
with col_controls[1]:
    show_anomalies = st.checkbox("Show anomalies on charts", value=True)
with col_controls[2]:
    download_all = st.button("⬇️ Export Filtered CSV")

start_year, end_year = year_range

filtered_yearly = yearly[(yearly["Year"] >= start_year) & (yearly["Year"] <= end_year)].copy()

if download_all:
    csv_bytes = filtered_yearly.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV (filtered)", csv_bytes, file_name=f"{primary_indicator}_yearly_{start_year}_{end_year}.csv")

# -------------------------
# Main layout: Tabs
# -------------------------
tab_trend, tab_summary, tab_downloads, tab_monthly, tab_forecast, tab_compare = st.tabs(
    ["📈 Trend", "📘 Summary", "⬇️ Downloads", "📅 Monthly", "📉 Forecast", "📊 Comparison"]
)

# -------------------------
# TAB: Trend
# -------------------------
with tab_trend:
    st.subheader(f"📈 {primary_indicator.upper()} — Trend ({start_year} → {end_year})")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(filtered_yearly["Year"], filtered_yearly["total_value"], marker="o", linewidth=2, label="Total")
    if show_anomalies:
        anoms = filtered_yearly[filtered_yearly["anomaly"]]
        if not anoms.empty:
            ax.scatter(anoms["Year"], anoms["total_value"], color="red", s=80, label="Anomaly")
            for _, r in anoms.iterrows():
                ax.annotate(f"{r['total_value']:,.0f}", (r["Year"], r["total_value"]), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8, color="red")

    ax.set_xlabel("Year")
    unit_label = df["Unit"].iloc[0] if "Unit" in df.columns and not df["Unit"].isna().all() else "unit"
    ax.set_ylabel(unit_label)
    ax.grid(alpha=0.2)
    ax.legend()
    st.pyplot(fig)

    # Save chart for downloads
    trend_path = OUT_DIR / f"{primary_indicator}_trend_{start_year}_{end_year}.png"
    fig.savefig(trend_path, dpi=150, bbox_inches="tight")

# -------------------------
# TAB: Summary
# -------------------------
with tab_summary:
    st.subheader("📘 KPI Summary")

    # KPI cards
    latest_row = filtered_yearly.iloc[-1]
    prev_row = filtered_yearly.iloc[-2] if len(filtered_yearly) > 1 else None

    col1, col2, col3 = st.columns(3)
    col1.metric(f"Latest ({int(latest_row['Year'])})", f"{latest_row['total_value']:,.2f} {unit_label}")
    if prev_row is not None:
        abs_change = latest_row["total_value"] - prev_row["total_value"]
        pct_change = (abs_change / prev_row["total_value"] * 100) if prev_row["total_value"] != 0 else 0.0
        col2.metric("Change (abs)", f"{abs_change:,.2f} {unit_label}")
        col3.metric("Change (%)", f"{pct_change:.2f}%")
    else:
        col2.metric("Change (abs)", "N/A")
        col3.metric("Change (%)", "N/A")

    st.markdown("### 🔢 Yearly Table")
    st.dataframe(filtered_yearly.style.format({"total_value": "{:,.2f}"}), use_container_width=True)

# -------------------------
# TAB: Downloads
# -------------------------
with tab_downloads:
    st.subheader("⬇️ Exports & Artifacts")
    st.write("Download generated charts and filtered data.")

    if trend_path.exists():
        with open(trend_path, "rb") as fh:
            st.download_button("📥 Download Trend PNG", fh, file_name=trend_path.name)

    csv_bytes = filtered_yearly.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Filtered CSV", csv_bytes, file_name=f"{primary_indicator}_yearly_{start_year}_{end_year}.csv")

# -------------------------
# TAB: Monthly
# -------------------------
with tab_monthly:
    st.subheader("📅 Monthly Analysis")

    years_av = sorted(df["Year"].astype(int).unique())
    sel_year = st.selectbox("Select year", years_av, index=len(years_av)-1)

    monthly_df = df[df["Year"] == sel_year].copy()
    if "Month" in monthly_df.columns:
        try:
            monthly_df["Month"] = monthly_df["Month"].astype(int)
        except Exception:
            pass
    else:
        st.info("Monthly data not available in source file.")
        monthly_df = monthly_df

    if monthly_df.empty:
        st.warning("No monthly rows for selected year.")
    else:
        monthly_df = monthly_df.sort_values("Month")
        monthly_df["anomaly"] = detect_anomalies(monthly_df["Value"], anomaly_threshold)

        figm, axm = plt.subplots(figsize=(10, 4))
        axm.bar(monthly_df["Month"], monthly_df["Value"], alpha=0.5, label="Monthly")
        axm.plot(monthly_df["Month"], monthly_df["Value"], marker="o", color="blue")
        if monthly_df["anomaly"].any() and show_anomalies:
            m_an = monthly_df[monthly_df["anomaly"]]
            axm.scatter(m_an["Month"], m_an["Value"], color="red", s=80, label="Anomaly")
            for _, r in m_an.iterrows():
                axm.annotate(f"{r['Value']:,.0f}", (r["Month"], r["Value"]), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8, color="red")

        axm.set_xticks(range(1, 13))
        axm.set_xlabel("Month")
        axm.set_ylabel(df["Unit"].iloc[0] if "Unit" in df.columns else "unit")
        axm.set_title(f"Monthly — {sel_year}")
        axm.grid(alpha=0.2)
        axm.legend()
        st.pyplot(figm)

        # metrics + table
        c1, c2, c3, c4 = st.columns(4)
        try:
            c1.metric("Max month", f"{int(monthly_df.loc[monthly_df['Value'].idxmax(),'Month'])} : {monthly_df['Value'].max():,.2f}")
            c2.metric("Min month", f"{int(monthly_df.loc[monthly_df['Value'].idxmin(),'Month'])} : {monthly_df['Value'].min():,.2f}")
        except Exception:
            c1.metric("Max month", "N/A")
            c2.metric("Min month", "N/A")
        c3.metric("Average", f"{monthly_df['Value'].mean():,.2f}")
        c4.metric("Anomalies", int(monthly_df['anomaly'].sum()))

        st.write("### 📄 Monthly Data")
        st.dataframe(monthly_df, use_container_width=True)

        # downloads
        m_png = OUT_DIR / f"{primary_indicator}_monthly_{sel_year}.png"
        figm.savefig(m_png, dpi=150, bbox_inches="tight")
        with open(m_png, "rb") as fh:
            st.download_button("📥 Download Monthly PNG", fh, file_name=m_png.name)
        st.download_button("📥 Download Monthly CSV", monthly_df.to_csv(index=False).encode("utf-8"), file_name=f"{primary_indicator}_monthly_{sel_year}.csv")

# -------------------------
# TAB: Forecast
# -------------------------
with tab_forecast:
    st.subheader("📉 Forecast")

    # Choose window length
    max_window = min(len(years_available), 10)
    window = st.slider("Use last N years for forecast", min_value=3, max_value=max_window, value=min(5, max_window))
    fw = yearly.tail(window).copy()

    try:
        next_year, pred_val = forecast_next_year(fw)
    except Exception:
        next_year, pred_val = None, None

    figf, axf = plt.subplots(figsize=(10, 4))
    axf.plot(fw["Year"], fw["total_value"], marker="o", linewidth=2, label="Historical")
    if next_year and pred_val is not None:
        axf.plot([fw["Year"].iloc[-1], next_year], [fw["total_value"].iloc[-1], pred_val],
                 linestyle="--", color="green", label=f"Forecast {next_year}")
        axf.scatter(next_year, pred_val, s=100, marker="X", color="green")
    axf.set_xlabel("Year")
    axf.set_ylabel(unit_label)
    axf.grid(alpha=0.2)
    axf.legend()
    st.pyplot(figf)

    if next_year and pred_val is not None:
        st.write(f"**Forecast for {next_year}:** {pred_val:,.2f} {unit_label}")

    # Download forecast PNG & CSV
    f_png = OUT_DIR / f"{primary_indicator}_forecast.png"
    figf.savefig(f_png, dpi=150, bbox_inches="tight")
    st.download_button("📥 Download Forecast PNG", open(f_png, "rb"), file_name=f_png.name)
    st.download_button("📥 Download Forecast Window CSV", fw.to_csv(index=False).encode("utf-8"), file_name=f"{primary_indicator}_forecast_window.csv")

# -------------------------
# TAB: Comparison
# -------------------------
with tab_compare:
    st.subheader("📊 Comparison — Multiple Indicators")

    choices = ["energy", "water", "emissions", "waste"]
    selected = st.multiselect("Select indicators to compare", choices, default=["energy", "emissions"])

    if len(selected) < 2:
        st.info("Choose at least two indicators to compare.")
    else:
        series_map = {}
        failed_loads = {}
        for ind in selected:
            try:
                dfi = agent._get_data(ind)
                try:
                    ydf = compute_yearly_totals(dfi)
                except Exception:
                    ydf = dfi.groupby("Year", as_index=False).agg(total_value=("Value", "sum"))
                    ydf["change_abs"] = ydf["total_value"].diff()
                    ydf["change_pct"] = ydf["total_value"].pct_change() * 100
                ydf["Year"] = ydf["Year"].astype(int)
                ydf = ydf[(ydf["Year"] >= start_year) & (ydf["Year"] <= end_year)].copy()
                series_map[ind] = ydf.set_index("Year")[["total_value"]].rename(columns={"total_value": ind})
            except Exception as e:
                failed_loads[ind] = str(e)

        if failed_loads:
            st.warning(f"Some indicators failed to load: {failed_loads}")

        if not series_map:
            st.error("No valid indicator series to compare.")
        else:
            # outer-join on year index
            combined = pd.concat(series_map.values(), axis=1, join="outer").sort_index()
            combined = combined.fillna(method="ffill").fillna(0).reset_index().rename(columns={"index": "Year"})
            figc, axc = plt.subplots(figsize=(10, 5))
            color_cycle = cycle(["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])
            for ind in selected:
                if ind in combined.columns:
                    axc.plot(combined["Year"], combined[ind], marker="o", linewidth=2, label=ind.capitalize(), color=next(color_cycle))
            axc.set_xlabel("Year")
            axc.set_ylabel("Value")
            axc.set_title("Indicator Comparison")
            axc.grid(alpha=0.2)
            axc.legend()
            st.pyplot(figc)

            st.write("### 🔢 Combined Table")
            st.dataframe(combined, use_container_width=True)
            st.download_button("📥 Download Comparison CSV", combined.to_csv(index=False).encode("utf-8"),
                               file_name=f"comparison_{'_'.join(selected)}_{start_year}_{end_year}.csv")

# End of file
