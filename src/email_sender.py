# src/email_sender.py

import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
from typing import Optional

# Force-load .env regardless of Streamlit load order
root_dir = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path=env_path)


def get_email_settings():
    """
    Load email configuration safely.
    This avoids raising errors during module import.
    """
    EMAIL_SENDER = os.getenv("ahmed.mounir.hse@gmail.com")
    EMAIL_PASSWORD = os.getenv("zoltdyghqfbggqyg")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        # Try fallback local config
        try:
            from .email_config import EMAIL_SENDER as fallback_sender
            from .email_config import EMAIL_PASSWORD as fallback_pass
            from .email_config import SMTP_SERVER as fallback_srv
            from .email_config import SMTP_PORT as fallback_port
            return fallback_sender, fallback_pass, fallback_srv, fallback_port
        except:
            # Do NOT raise error here → keep it for send function
            return None, None, None, None

    return EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT



def send_pdf_via_email(
    receiver_email: str,
    pdf_bytes: bytes,
    pdf_name: str,
    year: int,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
) -> bool:

    EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT = get_email_settings()

    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        raise RuntimeError("Email sender or password not configured.")

    # Build message
    msg = EmailMessage()
    msg["Subject"] = f"GRI Sustainability Report {year}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email

    if cc:
        msg["Cc"] = cc

    recipients = [receiver_email] + ([cc] if cc else []) + ([bcc] if bcc else [])

    msg.set_content(
        f"""
Hello,

Attached is the GRI Sustainability Report for the year {year}.

Best regards,
Sustainability AI Agent
"""
    )

    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=pdf_name,
    )

    # Send via SMTP
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg, from_addr=EMAIL_SENDER, to_addrs=recipients)

    return True
