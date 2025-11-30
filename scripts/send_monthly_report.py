#!/usr/bin/env python3
"""
scripts/send_monthly_report.py

What it does:
- Checks current date in Africa/Cairo timezone; if it's day 1 -> generates monthly reports (PDFs)
  for all indicators and emails them to recipients.
- If not day 1, exits (so you can schedule it to run daily).
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib
from email.message import EmailMessage
from typing import List

# Make sure project root and src are on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

# Project imports (use your agent + helpers)
from src.ai_agent.agent import SustainabilityAgentPro
from src.ai_agent.kpi_service import compute_yearly_totals
from src.ai_agent.agent import detect_anomalies, anomaly_stats  # if available, else local
# If detect_anomalies not exported, fallback to local implementation:
import pandas as pd
import numpy as np

def local_detect_anomalies(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    s = series.dropna()
    mu, sigma = s.mean(), s.std(ddof=0)
    if sigma == 0 or pd.isna(sigma):
        return pd.Series(False, index=series.index)
    z = (series - mu) / sigma
    return z.abs() > threshold

def today_is_first_of_month_in_cairo() -> bool:
    tz = ZoneInfo("Africa/Cairo")
    now = datetime.now(tz)
    return now.day == 1

def make_subject(month_name: str, year: int):
    return f"Sustainability GRI Monthly Report — {month_name} {year}"

def make_body(month_name: str, year: int, indicators: List[str]):
    lines = [
        f"Hello,",
        f"Attached: Monthly Sustainability GRI reports for {month_name} {year}.",
        "",
        "Included indicators: " + ", ".join(indicators),
        "",
        "Best regards,",
        "Sustainability Automated Reporter"
    ]
    return "\n".join(lines)

def attach_file(msg: EmailMessage, filepath: Path):
    with open(filepath, "rb") as f:
        data = f.read()
    maintype = "application"
    subtype = "pdf"
    msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filepath.name)

def send_email(smtp_host, smtp_port, smtp_user, smtp_pass, sender, recipients: List[str], msg: EmailMessage):
    # Use TLS SMTP
    with smtplib.SMTP(smtp_host, smtp_port, timeout=60) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg, from_addr=sender, to_addrs=recipients)

def generate_and_send():
    # ENV variables (remember to set these!)
    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASS = os.environ.get("SMTP_PASS")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", SMTP_USER)
    EMAIL_TO = os.environ.get("EMAIL_TO")  # comma separated
    INDICATORS_TO_SEND = os.environ.get("MONTHLY_INDICATORS", "energy,water,emissions,waste")

    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_TO):
        print("Missing SMTP or recipient environment variables. Set SMTP_HOST, SMTP_USER, SMTP_PASS, EMAIL_TO")
        return 1

    recipients = [x.strip() for x in EMAIL_TO.split(",") if x.strip()]
    indicators = [x.strip() for x in INDICATORS_TO_SEND.split(",") if x.strip()]

    # init agent
    agent = SustainabilityAgentPro()
    OUT = ROOT / "output"
    OUT.mkdir(parents=True, exist_ok=True)

    tz = ZoneInfo("Africa/Cairo")
    now = datetime.now(tz)
    month_name = now.strftime("%B")
    year = now.year

    generated_files = []

    for ind in indicators:
        try:
            print(f"Generating PDF for {ind} ...")
            # load data
            df = agent._get_data(ind)
            yearly = compute_yearly_totals(df)
            # compute anomalies (yearly totals)
            if "total_value" not in yearly.columns:
                yearly = yearly.rename(columns={yearly.columns[1]: "total_value"})  # fallback
            yearly["anomaly"] = local_detect_anomalies(yearly["total_value"])
            unit = df["Unit"].iloc[0] if "Unit" in df.columns else "unit"

            # Use agent.reporter.write_pdf (simple PDF with chart)
            pdf_path = agent.reporter.write_pdf(ind, yearly, yearly[yearly["anomaly"]], unit)
            # rename with month-year
            target = OUT / f"{ind}_monthly_{year}_{now.month:02d}.pdf"
            Path(pdf_path).rename(target)
            generated_files.append(target)
        except Exception as e:
            print(f"Failed to generate for {ind}: {e}")

    if not generated_files:
        print("No PDFs generated — aborting email.")
        return 1

    # Prepare email
    subject = make_subject(month_name, year)
    body = make_body(month_name, year, [p.stem for p in generated_files])
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    for fpath in generated_files:
        attach_file(msg, fpath)

    # send
    print("Sending email...")
    send_email(SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, recipients, msg)
    print("Email sent to:", recipients)
    return 0

def main():
    # run daily; only act when Cairo date is 1
    if not today_is_first_of_month_in_cairo():
        print("Not the first of the month in Cairo — exiting.")
        return 0
    return generate_and_send()

if __name__ == "__main__":
    sys.exit(main())
