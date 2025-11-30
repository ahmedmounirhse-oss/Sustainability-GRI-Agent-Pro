import smtplib, os
from email.message import EmailMessage

EMAIL = "ahmed.mounir.hse@gmail.com"
PASS = "gjqmoixtzthrqgke"

msg = EmailMessage()
msg["From"] = EMAIL
msg["To"] = EMAIL
msg["Subject"] = "Test"
msg.set_content("test ok")

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL, PASS)
        smtp.send_message(msg)
    print("OK")
except Exception as e:
    print("ERROR:", e)
