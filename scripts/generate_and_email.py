import os
from datetime import datetime
from src.report_generator import build_gri_pdf_report
from src.email_sender import send_pdf_via_email

# ------------- GENERATE REPORT -------------

# Auto detect latest year
DATA_DIR = "data"
years = []

import pandas as pd
import glob

for f in glob.glob(f"{DATA_DIR}/*.xlsx"):
    try:
        df = pd.read_excel(f, sheet_name=0)  # any sheet
        if "Year" in df.columns:
            years.extend(df["Year"].dropna().astype(int).unique().tolist())
    except:
        pass

if not years:
    raise RuntimeError("No year found in data files!")

year = max(years)
print("Generating report for year:", year)

pdf_buffer = build_gri_pdf_report(year)
pdf_bytes = pdf_buffer.getvalue()

pdf_name = f"GRI_Report_{year}.pdf"

# ------------- SEND EMAIL -------------

receiver = os.getenv("EMAIL_TO")
if not receiver:
    raise RuntimeError("EMAIL_TO is not configured in secrets.")

send_pdf_via_email(
    receiver_email=receiver,
    pdf_bytes=pdf_bytes,
    pdf_name=pdf_name,
    year=year
)

print("Report sent successfully to:", receiver)
