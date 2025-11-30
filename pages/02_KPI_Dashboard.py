import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

from src.ai_agent.agent import SustainabilityAgentPro
from src.ai_agent.kpi_service import compute_yearly_totals
from src.ai_agent.data_loader import load_indicator

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("📊 Sustainability KPI Dashboard — EGY-WOOD")

# -----------------------------
# SAFE RERUN FUNCTION
# -----------------------------
def safe_rerun():
    try:
        st.rerun()
    except:
        pass

# -----------------------------
# LOAD AGENT (Session Safe)
# -----------------------------
if "agent" not in st.session_state:
    st.session_state.agent = SustainabilityAgentPro()
agent = st.session_state.agent

# -----------------------------
# SIDEBAR CONTROLS
# -----------------------------
with st.sidebar:
    st.header("Data Controls")
    indicator = st.selectbox(
        "Select Indicator",
        ["energy", "water", "emissions", "waste"]
    )

    if st.button("🔄 Refresh Data"):
        if "cached_data" in st.session_state:
            del st.session_state["cached_data"]
        st.toast("Data refreshed successfully!")
        safe_rerun()

# -----------------------------
# DATA LOADING (with caching)
# -----------------------------
@st.cache_data(ttl=5)
def load_clean_data(indicator_key):
    df = load_indicator(indicator_key)
    yearly = compute_yearly_totals(df)
    return df, yearly

try:
    df, yearly = load_clean_data(indicator)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# -----------------------------
# KPI HEADERS
# -----------------------------
col1, col2, col3 = st.columns(3)

latest_year = yearly["Year"].max()
latest_val = yearly[yearly["Year"] == latest_year]["total_value"].values[0]

prev_year = latest_year - 1
prev_val = yearly[yearly["Year"] == prev_year]["total_value"].values[0] if prev_year in yearly["Year"].values else None

change = None
if prev_val:
    change = ((latest_val - prev_val) / prev_val) * 100

col1.metric("Latest Year", latest_year)
col2.metric("Total Value", f"{latest_val:,.2f}")
col3.metric("Change YoY", f"{change:.2f}%" if change else "—")

# -----------------------------
# YEARLY TREND CHART
# -----------------------------
st.subheader("📈 Yearly Trend")

fig1, ax1 = plt.subplots(figsize=(8, 3.8))
ax1.plot(yearly["Year"], yearly["total_value"], marker="o")
ax1.set_xlabel("Year")
ax1.set_ylabel(df["Unit"].iloc[0] if "Unit" in df.columns else "")
ax1.grid(True)
st.pyplot(fig1)

# -----------------------------
# MONTHLY CHART (if available)
# -----------------------------
if "Month" in df.columns:
    st.subheader(f"📅 Monthly Breakdown — {latest_year}")

    df_latest = df[df["Year"] == latest_year]
    df_mon = df_latest.groupby("Month").agg(Value=("Value", "sum")).reset_index()

    fig2, ax2 = plt.subplots(figsize=(8, 3.8))
    ax2.bar(df_mon["Month"], df_mon["Value"])
    ax2.plot(df_mon["Month"], df_mon["Value"], marker="o")
    ax2.set_xlabel("Month")
    ax2.set_ylabel(df["Unit"].iloc[0] if "Unit" in df.columns else "")
    ax2.grid(True)

    st.pyplot(fig2)

# -----------------------------
# RAW DATA TABLE
# -----------------------------
st.subheader("📂 Raw Data")
st.dataframe(df)

# -----------------------------
# YEARLY SUMMARY TABLE
# -----------------------------
st.subheader("📘 Yearly Summary")
st.dataframe(yearly)
