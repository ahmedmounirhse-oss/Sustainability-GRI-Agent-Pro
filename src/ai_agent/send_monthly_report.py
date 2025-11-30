# scripts/send_monthly_report.py
import os
from datetime import datetime
from src.report_generator import build_gri_pdf_report
from src.email_sender import send_pdf_via_email

def main():
    # month/year selection: default last completed month or current year selection
    now = datetime.utcnow()
    year = int(os.getenv("REPORT_YEAR", str(now.year)))
    indicators = os.getenv("REPORT_INDICATORS", "energy,water,emissions,waste").split(",")
    indicators = [i.strip() for i in indicators if i.strip()]

    buf = build_gri_pdf_report(
        year=year,
        indicators=indicators,
        include_monthly=True,
        include_forecast=True,
        include_anomalies=True,
        basis_for_intensity=None,
        logo_path=os.getenv("REPORT_LOGO", "assets/company_logo.png"),
    )

    pdf_name = f"GRI_Report_{year}.pdf"
    pdf_bytes = buf.read()

    recipients = os.getenv("EMAIL_TO")
    if not recipients:
        print("No EMAIL_TO configured — aborting send.")
        return

    emails = [e.strip() for e in recipients.split(",") if e.strip()]
    for em in emails:
        try:
            send_pdf_via_email(receiver_email=em, pdf_bytes=pdf_bytes, pdf_name=pdf_name)
            print(f"Sent to {em}")
        except Exception as e:
            print(f"Failed to send to {em}: {e}")

if __name__ == "__main__":
    main()
