import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from src.logger import logger

def send_alert_notification(
    recipient_email: Optional[str],
    project_title: str,
    alert_type: str,
    reasons: List[str],
    suggested_action: str
) -> bool:
    """
    Sends an email notification via SMTP if configured in .env;
    gracefully falls back to console & rotating log file if SMTP is unconfigured.
    """
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", "alerts@college.edu")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    subject = f"[PROJECT RISK ALERT] {alert_type}: {project_title}"
    body = (
        f"Project Alert Notification\n"
        f"--------------------------\n"
        f"Project: {project_title}\n"
        f"Alert Type: {alert_type}\n\n"
        f"Risk Factors Detected:\n" +
        "\n".join(f"- {r}" for r in reasons) +
        f"\n\nSuggested Action:\n{suggested_action}\n"
    )

    if not smtp_host or not recipient_email:
        # Fallback to structured logging
        logger.info(f"[NOTIFICATION FALLBACK] To: {recipient_email or 'Guide'} | {subject} | Action: {suggested_action}")
        return True

    try:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        if use_tls:
            server.starttls()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        logger.info(f"Successfully sent alert email to {recipient_email} for project '{project_title}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send email notification to {recipient_email}: {e}. Falling back to logs.")
        logger.info(f"[NOTIFICATION FALLBACK] {subject} | Action: {suggested_action}")
        return False
