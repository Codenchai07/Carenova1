import smtplib
from email.message import EmailMessage
import os

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_email(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print("📧 Email sent to", to_email)

    except Exception as e:
        print("❌ Email error:", e)


# existing code stays exactly same 👆

ADMIN_EMAIL = os.getenv("EMAIL_ADDRESS")


def send_contact_notification_to_admin(name, email, message):
    subject = "📩 New Contact Form Submission - CareNova"

    body = f"""
New contact form submission received:

Name: {name}
Email: {email}

Message:
{message}
"""

    send_email(ADMIN_EMAIL, subject, body)
