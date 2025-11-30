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

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import glob
from pathlib import Path

from src.ai_agent.data_loader import normalize_month

st.set_page_config(page_title="Data Explorer", layout="wide")

st.title("📂 Data Explorer")
st.write("استعراض وتحليل البيانات الخام مباشرة من ملفات Excel داخل مجلد data/.")

# ---------------------------------------------------------
# 1) AUTO DISCOVER EXCEL FILES
# ---------------------------------------------------------
st.subheader("🗂 اختر ملف البيانات")

files = glob.glob("data/*.xlsx")  # returns list of file paths

if not files:
    st.error("❌ لم يتم العثور على أي ملفات Excel داخل مجلد data/")
    st.stop()

file_names = [Path(f).name for f in files]

selected_file = st.selectbox("اختر ملف Excel:", file_names)

file_path = Path("data") / selected_file

# ---------------------------------------------------------
# 2) LOAD SHEETS IN THE FILE
# ---------------------------------------------------------
xls = pd.ExcelFile(file_path)
sheets = xls.sheet_names

st.subheader("📑 اختر الشيت داخل الملف")
selected_sheet = st.selectbox("Sheet:", sheets)

# ---------------------------------------------------------
# LOAD DATA FROM SELECTED SHEET
# ---------------------------------------------------------
df = pd.read_excel(file_path, sheet_name=selected_sheet)

st.write("### 📄 محتوى الشيت")
st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# OPTIONAL: Normalize Month Values
# ---------------------------------------------------------
if "Month" in df.columns:
    try:
        df["Month"] = df["Month"].apply(normalize_month)
    except:
        pass

# ---------------------------------------------------------
# 3) QUICK PLOT (if Value column exists)
# ---------------------------------------------------------
if "Value" in df.columns:

    st.subheader("📊 Quick Plot (Preview)")

    if "Year" in df.columns and "Month" in df.columns:
        df_plot = df.copy()

        # Fix types
        df_plot["Year"] = df_plot["Year"].astype(int)
        df_plot["Month"] = df_plot["Month"].astype(int)

        # Sort values
        df_plot = df_plot.sort_values(["Year", "Month"])

        year_choice = st.selectbox("اختر سنة للعرض:", sorted(df_plot["Year"].unique()))

        df_year = df_plot[df_plot["Year"] == year_choice]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df_year["Month"], df_year["Value"], marker="o", linewidth=2)
        ax.set_title(f"{selected_sheet} — السنة {year_choice}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Value")
        ax.grid(alpha=0.2)

        st.pyplot(fig)

    else:
        st.info("⚠ لا يمكن رسم المخطط لأن الأعمدة Year و Month غير موجودة.")

# ---------------------------------------------------------
# 4) CSV DOWNLOAD
# ---------------------------------------------------------
csv_data = df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download CSV", csv_data, file_name=f"{selected_sheet}.csv")

