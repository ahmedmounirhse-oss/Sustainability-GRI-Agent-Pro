import smtplib
from email.message import EmailMessage
import ssl

EMAIL = "ahmed.mounir.hse@gmail.com"
PASS = "gjqmoixtzthrqgke"   # App Password

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

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(EMAIL, PASS)
            smtp.send_message(msg)

        return True  # لو وصلت هنا، الإرسال ناجح 100%

    except smtplib.SMTPResponseException as e:
        # Gmail ساعات يرجع warning بعد الإرسال
        # كود 250 أو 235 معناهم نجاح
        if e.smtp_code in (250, 235):
            return True
        return False

    except Exception:
        return False
