import os
import smtplib
from email.message import EmailMessage

LOCAL_SMTP_ONLY = True  # <— المهم

def send_pdf_via_email(receiver_email, pdf_bytes, pdf_name, year):
    if LOCAL_SMTP_ONLY and os.getenv("STREAMLIT_RUNTIME") == "cloud":
        # Skip email silently on cloud
        print("Email skipped: running on Streamlit Cloud")
        return

    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = receiver_email
    msg["Subject"] = f"EGY-WOOD GRI Report {year}"
    msg.set_content("Please find attached the automated GRI report.")

    msg.add_attachment(pdf_bytes,
                       maintype="application",
                       subtype="pdf",
                       filename=pdf_name)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
