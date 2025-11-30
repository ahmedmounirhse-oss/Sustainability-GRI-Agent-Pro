import os
from dotenv import load_dotenv

# Load .env
load_dotenv(dotenv_path=".env")

import streamlit as st

# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(
    page_title="Sustainability GRI Agent",
    page_icon="🌍",
    layout="wide"
)

# -------------------------------------------------------
# LOGO
# -------------------------------------------------------
logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/UN_SDG_Logo_Color.png/640px-UN_SDG_Logo_Color.png"

st.markdown(
    f"""
    <div style="text-align:center; margin-top:20px;">
        <img src="{logo_url}" width="150">
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------------
# TITLE
# -------------------------------------------------------
st.markdown("""
<h1 style='text-align:center; color:#2E7D32; margin-top:10px;'>
    🌍 Sustainability GRI Reporting Agent
</h1>

<p style='text-align:center; font-size:20px;'>
    Automated Sustainability Data Analysis • KPI Engine • GRI Compliance • AI Narratives • PDF Generator
</p>
""", unsafe_allow_html=True)

st.write("")
st.write("")

# -------------------------------------------------------
# TEAM SECTION
# -------------------------------------------------------
team_members = [
"AbdelHamid Mamdouh Zedan",
"Ahmed Mounir Saad Ghaith",
"Akram Mohamed Mohamed",
"Mohamed Mohamed Mounir Abd El-Maboud",
"Medhat Mohamed Ahmed",
"Ahmed Youssef Mahmoud Sharaf",
"Ahmed Hisham Mohamed Moustafa",
"Mahmoud Mohamed Fouad Hussein",
"Ibrahim Wagih Ibrahim Ali",
"Hassan Adel Hassan Zaied",
"Wasfy Ead Elsaeed Metouly",
"Mohamed ElSayed Menshawy",
"Mohamed Salah Abd Elsalam",
"Mostafa Hussien",
"Abdelrhman Alaa ElDien Mohamed"
]

st.markdown("""
<h2 style='color:#1565C0; text-align:center; margin-bottom:10px;'>👥 Project Team Members</h2>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
for i, name in enumerate(team_members):
    if i % 3 == 0:
        col1.write(f"- {name}")
    elif i % 3 == 1:
        col2.write(f"- {name}")
    else:
        col3.write(f"- {name}")

st.write("")
st.write("")

# -------------------------------------------------------
# SUPERVISOR
# -------------------------------------------------------
st.markdown("""
<h3 style='text-align:center; color:#C62828;'>
    🎓 Under the Supervision of: <b>Dr. Mohamed Tash</b>
</h3>
""", unsafe_allow_html=True)

st.write("")
st.write("")

# -------------------------------------------------------
# FEATURE CARDS
# -------------------------------------------------------
st.markdown("""
<h2 style='text-align:center; color:#2E7D32;'>🚀 System Features</h2>
""", unsafe_allow_html=True)

colA, colB, colC = st.columns(3)

with colA:
    st.markdown("""
    <div style="padding:20px; border-radius:12px; background-color:#E8F5E9; 
    box-shadow:0 1px 6px rgba(0,0,0,0.1); text-align:center;">
        <h3 style="color:#1b5e20;">📊 KPI Dashboard</h3>
        <p>Interactive KPIs for Energy, Water, Emissions, and Waste.</p>
    </div>
    """, unsafe_allow_html=True)

with colB:
    st.markdown("""
    <div style="padding:20px; border-radius:12px; background-color:#E3F2FD; 
    box-shadow:0 1px 6px rgba(0,0,0,0.1); text-align:center;">
        <h3 style="color:#0d47a1;">💬 AI Chat Agent</h3>
        <p>GRI-aligned insights powered by Groq LLM.</p>
    </div>
    """, unsafe_allow_html=True)

with colC:
    st.markdown("""
    <div style="padding:20px; border-radius:12px; background-color:#FFF3E0; 
    box-shadow:0 1px 6px rgba(0,0,0,0.1); text-align:center;">
        <h3 style="color:#e65100;">📄 PDF Generator</h3>
        <p>Exports a full GRI Sustainability Report.</p>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# -------------------------------------------------------
# NAVIGATION
# -------------------------------------------------------
st.subheader("🔗 Quick Navigation")

nav1, nav2, nav3, nav4 = st.columns(4)

with nav1:
    st.page_link("pages/01_Chat_Agent.py", label="💬 Chat Agent")

with nav2:
    st.page_link("pages/02_KPI_Dashboard.py", label="📊 KPI Dashboard")

with nav3:
    st.page_link("pages/03_Data_Explorer.py", label="📂 Data Explorer")

with nav4:
    st.page_link("pages/04_GRI_Report_PDF.py", label="📄 PDF Report Generator")

st.write("")
st.write("")

# -------------------------------------------------------
# FOOTER
# -------------------------------------------------------
st.markdown("""
<hr>
<p style='text-align:center; color:gray; font-size:14px;'>
Developed by Sustainability Team | Powered by Streamlit & Groq LLM
</p>
""", unsafe_allow_html=True)
