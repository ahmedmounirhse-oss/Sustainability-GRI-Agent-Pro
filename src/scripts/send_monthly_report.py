import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def generate_monthly_pdf():
    now = datetime.utcnow().strftime("%Y-%m-%d  %H:%M UTC")
    pdf_file = "GRI_Monthly_Report.pdf"

    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    styles = getSampleStyleSheet()

    story = [
        Paragraph("<b>Monthly Sustainability GRI Report</b>", styles["Title"]),
        Paragraph(f"Generated automatically at: {now}", styles["Normal"])
    ]

    doc.build(story)
    return pdf_file


def send_email(pdf_path):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    email_from = os.getenv("EMAIL_FROM")
    email_to = os.getenv("EMAIL_TO")

    msg = EmailMessage()
    msg["Subject"] = "Monthly GRI Sustainability Report"
    msg["From"] = email_from
    msg["To"] = email_to
    msg.set_content("Please find the automated monthly GRI sustainability report attached.")

    with open(pdf_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="GRI_Monthly_Report.pdf")

    with smtplib.SMTP_SSL(host, port) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)

    print("Email sent successfully.")


if __name__ == "__main__":
    pdf = generate_monthly_pdf()
    send_email(pdf)
