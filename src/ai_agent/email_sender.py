import os
import smtplib
from email.message import EmailMessage
from datetime import datetime


def send_pdf_via_email(receiver_email: str, pdf_bytes: bytes, pdf_name: str, year: int):
    """
    Sends PDF report via SMTP using .env or GitHub Secrets
    """

    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS]):
        raise RuntimeError("SMTP settings are missing (SMTP_HOST / SMTP_USER / SMTP_PASS).")

    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = receiver_email
    msg["Subject"] = f"GRI Sustainability Report – {year}"

    msg.set_content(f"""
Hello,

Attached is the automatically generated GRI Sustainability Report for {year}.

Sent automatically by Sustainability-GRI-Agent.

Regards,
Automation System
""")

    # attach pdf
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=pdf_name
    )

    # send
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    return True
