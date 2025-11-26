import streamlit as st
import pandas as pd

from src.data_loader import load_indicator


st.set_page_config(page_title="Data Explorer", layout="wide")

st.title("🔍 Data Explorer")
st.write("Browse, filter, and analyze raw sustainability data.")


# ---------- SIDEBAR ----------
st.sidebar.header("Filter Options")

indicator_map = {
    "Energy Consumption": "energy",
    "Water Usage": "water",
    "GHG Emissions": "emissions",
    "Waste Generation": "waste",
}

indicator_choice = st.sidebar.selectbox("Select Indicator", list(indicator_map.keys()))
indicator_key = indicator_map[indicator_choice]


# ---------- LOAD DATA ----------
df = load_indicator(indicator_key)

# Normalize Month as string to ensure filtering consistency
df["Month"] = df["Month"].astype(str)


# ---------- FILTER OPTIONS ----------
years_available = sorted(df["Year"].unique())
months_available = sorted(df["Month"].unique())

year_filter = st.sidebar.multiselect("Filter by Year", years_available, default=years_available)
month_filter = st.sidebar.multiselect("Filter by Month", months_available, default=months_available)


# ---------- APPLY FILTER ----------
filtered_df = df[
    (df["Year"].isin(year_filter)) &
    (df["Month"].isin(month_filter))
]


# ---------- SHOW FILTERED DATA ----------
st.subheader("📄 Filtered Data")
if filtered_df.empty:
    st.warning("No data found for the selected filters.")
else:
    st.dataframe(filtered_df, use_container_width=True)


# ---------- SUMMARY ----------
if not filtered_df.empty:
    st.subheader("📊 Summary Statistics")

    summary = (
        filtered_df.groupby("Year", as_index=False)
        .agg(
            total_value=("Value", "sum"),
            avg_value=("Value", "mean"),
            max_value=("Value", "max"),
            min_value=("Value", "min"),
        )
    )

    st.dataframe(summary, use_container_width=True)


# ---------- DOWNLOAD ----------
if not filtered_df.empty:
    st.subheader("⬇️ Download Filtered Data")

    csv = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"{indicator_key}_filtered_data.csv",
        mime="text/csv"
    )
