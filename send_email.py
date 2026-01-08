import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

def send_email():
    sender = os.environ.get('GMAIL_USERNAME')
    password = os.environ.get('GMAIL_APP_PASSWORD')
    recipient = "ttmmghmm+gemini@gmail.com"
    
    if not sender or not password:
        print("Error: GMAIL_USERNAME or GMAIL_APP_PASSWORD not set.")
        return

    # Read HTML content
    try:
        with open('report.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("Error: report.html not found.")
        return

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Stratford Events Weekly Report - {os.environ.get('GITHUB_RUN_ID', 'Manual')}"
    msg['From'] = f"Stratford Events Bot <{sender}>"
    msg['To'] = recipient
    msg['Date'] = formatdate(localtime=True)

    # Plain text fallback
    text_content = "Please enable HTML to view this report."
    part1 = MIMEText(text_content, 'plain')
    part2 = MIMEText(html_content, 'html')

    msg.attach(part1)
    msg.attach(part2)

    # Send
    try:
        print(f"Connecting to smtp.gmail.com:465...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
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
