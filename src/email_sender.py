import smtplib
from email.message import EmailMessage
import ssl

def send_pdf_via_email(receiver_email, pdf_bytes, pdf_name, year):

    try:
        msg = EmailMessage()
        msg["From"] = os.getenv("EMAIL_ADDRESS")
        msg["To"] = receiver_email
        msg["Subject"] = f"GRI Sustainability Report - {year}"
        msg.set_content("Please find attached your sustainability report.")

        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=pdf_name
        )

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
            smtp.send_message(msg)

        return True   # تأكيد نجاح الإرسال

    except smtplib.SMTPResponseException as e:
        # Gmail أحيانًا يعمل warning بعد الإرسال
        # لكن الرسالة تكون اتبعت بالفعل
        if e.smtp_code == 250 or e.smtp_code == 235:
            return True
        return False

    except Exception:
        return False
