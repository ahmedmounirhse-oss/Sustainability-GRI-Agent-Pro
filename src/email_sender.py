# src/email_sender.py
import os
import time
import smtplib
from email.message import EmailMessage
from typing import Optional

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

def send_pdf_via_email(
    receiver_email: str,
    pdf_bytes: bytes,
    pdf_name: str,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_pass: Optional[str] = None,
    sender: Optional[str] = None,
    retries: int = 2,
    retry_delay: int = 5,
):
    """
    Send PDF bytes to a single receiver. Use env vars as defaults.
    Raises exception on permanent failure.
    """
    smtp_host = smtp_host or SMTP_HOST
    smtp_port = smtp_port or SMTP_PORT
    smtp_user = smtp_user or SMTP_USER
    smtp_pass = smtp_pass or SMTP_PASS
    sender = sender or EMAIL_FROM

    if subject is None:
        subject = f"GRI Sustainability Report — {pdf_name}"
    if body is None:
        body = f"Attached: {pdf_name}"

    if not smtp_host or not smtp_user or not smtp_pass:
        raise RuntimeError("SMTP configuration missing. Set SMTP_HOST/SMTP_USER/SMTP_PASS in environment.")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.set_content(body)
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=pdf_name)

    last_exc = None
    for attempt in range(retries + 1):
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=60) as s:
                s.starttls()
                s.login(smtp_user, smtp_pass)
                s.send_message(msg)
            return True
        except Exception as e:
            last_exc = e
            if attempt < retries:
                time.sleep(retry_delay)
                continue
            raise last_exc
