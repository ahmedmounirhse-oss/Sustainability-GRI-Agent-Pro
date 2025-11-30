import smtplib
from email.message import EmailMessage
import os

EMAIL = os.getenv("EMAIL_ADDRESS")
PASS = os.getenv("EMAIL_PASSWORD")

def send_pdf_via_email(receiver_email, pdf_bytes, pdf_name, year):
    msg = EmailMessage()
    msg["Subject"] = f"EGY-WOOD GRI Sustainability Report {year}"
    msg["From"] = EMAIL
    msg["To"] = receiver_email
    msg.set_content("Please find the attached GRI Sustainability Report.")

    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=pdf_name
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL, PASS)
        smtp.send_message(msg)
