import os
import smtplib
import json
from email.message import EmailMessage
from urllib import request


def print_console_alert(alert: dict):
    print("[ALERT]")
    print(f"Severity: {alert['severity']}")
    print(f"Category: {alert['category']}")
    print(f"Service: {alert['source_service']}")
    print(f"Type: {alert['alert_type']}")
    print(f"Message: {alert['message']}")


def send_email_alert(alert: dict) -> bool:
    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT", "587"))
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("ALERT_RECEIVER")

    if not all([host, user, password, receiver]):
        print("[ALERT EMAIL SKIPPED] Missing EMAIL_HOST/EMAIL_USER/EMAIL_PASSWORD/ALERT_RECEIVER.")
        return False

    message = EmailMessage()
    message["Subject"] = f"[{alert['severity']}] {alert['alert_type']} - {alert['source_service']}"
    message["From"] = user
    message["To"] = receiver
    message.set_content(
        "\n".join(
            [
                f"Severity: {alert['severity']}",
                f"Category: {alert['category']}",
                f"Service: {alert['source_service']}",
                f"Type: {alert['alert_type']}",
                f"Message: {alert['message']}",
                f"Log ID: {alert['log_id']}",
            ]
        )
    )

    with smtplib.SMTP(host, port, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(message)

    print("[ALERT EMAIL SENT]", receiver)
    return True


def send_webhook_alert(alert: dict) -> bool:
    webhook_url = os.getenv("ALERT_WEBHOOK_URL")
    if not webhook_url:
        return False

    payload = {
        "text": f"[{alert['severity']}] {alert['alert_type']} in {alert['source_service']}: {alert['message']}",
        "alert": alert,
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        response.read()
    print("[ALERT WEBHOOK SENT]")
    return True


def notify_developers(alert: dict, send_email: bool):
    print_console_alert(alert)
    try:
        send_webhook_alert(alert)
    except Exception as exc:
        print("[ALERT WEBHOOK FAILED]", exc)

    if send_email:
        try:
            send_email_alert(alert)
        except Exception as exc:
            print("[ALERT EMAIL FAILED]", exc)
