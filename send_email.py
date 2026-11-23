import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from params import (
    EMAIL_ENV_PASSWORD_KEY,
    EMAIL_ENV_USERNAME_KEY,
    EMAIL_FROM_NAME,
    EMAIL_PLAINTEXT_FALLBACK,
    EMAIL_SUBJECT_TEMPLATE,
    REPORT_OUTPUT_FILE,
    SHORT_DATE_FORMAT,
    SMTP_HOST,
    SMTP_PORT,
)

def send_email():
    sender = os.environ.get(EMAIL_ENV_USERNAME_KEY)
    password = os.environ.get(EMAIL_ENV_PASSWORD_KEY)
    recipient = "ttmmghmm+gemini@gmail.com"
    
    if not sender or not password:
        print(f"Error: {EMAIL_ENV_USERNAME_KEY} or {EMAIL_ENV_PASSWORD_KEY} not set.")
        return

    # Read HTML content
    try:
        with open(REPORT_OUTPUT_FILE, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: {REPORT_OUTPUT_FILE} not found.")
        return

    # Create message
    msg = MIMEMultipart('alternative')
    from datetime import datetime
    week_of = datetime.now().strftime(SHORT_DATE_FORMAT)
    msg['Subject'] = EMAIL_SUBJECT_TEMPLATE.format(week_of=week_of)
    msg['From'] = f"{EMAIL_FROM_NAME} <{sender}>"
    msg['To'] = recipient
    msg['Date'] = formatdate(localtime=True)

    # Plain text fallback
    text_content = EMAIL_PLAINTEXT_FALLBACK
    part1 = MIMEText(text_content, 'plain')
    part2 = MIMEText(html_content, 'html')

    msg.attach(part1)
    msg.attach(part2)

    # Send
    try:
        print(f"Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            print("Logging in...")
            server.login(sender, password)
            print("Sending email...")
            server.sendmail(sender, recipient, msg.as_string())
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise

if __name__ == "__main__":
    send_email()
