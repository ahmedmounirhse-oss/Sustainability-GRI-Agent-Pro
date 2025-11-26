import streamlit as st
import pandas as pd

from src.data_loader import load_indicator
from src.kpi_service import compute_yearly_totals
from src.reporting import build_indicator_narrative


st.set_page_config(page_title="KPI Dashboard", layout="wide")

st.title("📊 Sustainability KPI Dashboard")
st.write("Analyze Energy, Water, Emissions, and Waste indicators using annual KPIs, trends, and comparisons.")


# ---------- SIDEBAR ----------
st.sidebar.header("Indicator Selection")

indicators = {
    "Energy Consumption": "energy",
    "Water Usage": "water",
    "GHG Emissions": "emissions",
    "Waste Generation": "waste"
}

user_choice = st.sidebar.selectbox("Select Indicator", list(indicators.keys()))
indicator_key = indicators[user_choice]


# ---------- LOAD DATA ----------
df = load_indicator(indicator_key)
yearly = compute_yearly_totals(df)

unit = df["Unit"].iloc[0]
years_available = sorted(df["Year"].unique())

st.sidebar.subheader("Data Summary")
st.sidebar.write(f"**Unit:** {unit}")
st.sidebar.write(f"**Years available:** {years_available[0]} → {years_available[-1]}")


# ---------- RAW DATA TABLE ----------
st.subheader("📄 Raw Indicator Data")
st.dataframe(df, use_container_width=True)


# ---------- KPI CARDS ----------
st.subheader("📌 KPI Summary")

col1, col2, col3 = st.columns(3)

latest_year = int(df["Year"].max())
latest_row = yearly[yearly["Year"] == latest_year].iloc[0]

with col1:
    st.metric(
        label=f"Total ({latest_year})",
        value=f"{latest_row['total_value']:,.1f} {unit}"
    )

with col2:
    yoy = latest_row["change_abs"]
    st.metric(
        label="YoY Change",
        value="n/a" if pd.isna(yoy) else f"{yoy:,.1f} {unit}"
    )

with col3:
    yoy_pct = latest_row["change_pct"]
    st.metric(
        label="YoY % Change",
        value="n/a" if pd.isna(yoy_pct) else f"{yoy_pct:,.1f}%"
    )


# ---------- TREND CHART ----------
st.subheader("📈 Yearly Trend Chart")

chart_df = yearly.copy()
chart_df["Year"] = chart_df["Year"].astype(str)

st.line_chart(
    chart_df.set_index("Year")["total_value"],
    height=350
)


# ---------- YEAR-TO-YEAR COMPARISON ----------
st.subheader("📊 Year-to-Year Comparison")

colA, colB = st.columns(2)

year1 = colA.selectbox("Select Year A", years_available, index=0)
year2 = colB.selectbox("Select Year B", years_available, index=len(years_available)-1)

if year1 != year2:
    total1 = yearly[yearly["Year"] == year1]["total_value"].iloc[0]
    total2 = yearly[yearly["Year"] == year2]["total_value"].iloc[0]

    diff_abs = total2 - total1
    diff_pct = (diff_abs / total1) * 100.0 if total1 != 0 else float("nan")

    st.write(f"### Comparing **{year1} → {year2}**")
    st.write(f"- **{year1} Total:** {total1:,.1f} {unit}")
    st.write(f"- **{year2} Total:** {total2:,.1f} {unit}")
    st.write(f"- **Difference:** {diff_abs:,.1f} ({diff_pct:,.1f}%)")


# ---------- GRI NARRATIVE ----------
st.subheader("📝 GRI Narrative")

selected_year = st.selectbox("Select year for narrative", years_available)

try:
    narrative = build_indicator_narrative(indicator_key, df, selected_year)
    st.info(narrative)
except Exception as e:
    st.error(f"Error generating narrative: {e}")
st.sidebar.subheader("Upload New Data File")

uploaded_file = st.sidebar.file_uploader(
    "Upload Excel file (e.g. Sustainability_data 2026.xlsx)",
    type=["xlsx"]
)

if uploaded_file is not None:
    save_path = f"data/{uploaded_file.name}"
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.sidebar.success(f"File uploaded and saved as: {uploaded_file.name}")

    # Force reloading cache of the agent (auto-refresh data)
    agent = SustainabilityAgent()  # reinitialize agent cache
    st.sidebar.info("Data reloaded successfully! Dashboard updated.")
