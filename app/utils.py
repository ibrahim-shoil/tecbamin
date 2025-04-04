import re

import smtplib
from email.mime.text import MIMEText


def generate_slug(text):
    """
    يحوّل النص إلى slug يدعم العربية والإنجليزية ويستخدم في الروابط.
    مثال: "ما هو الذكاء الاصطناعي؟" ← "ما-هو-الذكاء-الاصطناعي"
    """
    # إزالة أي رموز غير الأحرف العربية أو الإنجليزية أو الأرقام أو المسافات أو الشرطة
    text = re.sub(r"[^\u0621-\u064Aa-zA-Z0-9\s-]", "", text)

    # استبدال أي عدد من المسافات أو الشرطات بشرطة واحدة
    text = re.sub(r"[\s\-]+", "-", text)

    # إزالة الشرطات من البداية والنهاية
    return text.strip("-").lower()


def send_email_smtp(subject, body, sender_email, sender_name):
    recipient = "you@yourdomain.com"  # ✉️ غيّرها لبريدك
    smtp_host = "smtp.hostinger.com"
    smtp_port = 587
    smtp_username = "you@yourdomain.com"  # نفس البريد
    smtp_password = "your_password"  # كلمة السر من هوستنجر

    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
