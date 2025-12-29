from crewai import Agent
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Union

from config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SMTP_FROM,
)


emailer = Agent(
    role="Emailer",
    goal="Compose and send concise emails with the provided content to specified recipients.",
    backstory="A professional assistant skilled at preparing and dispatching emails.",
    allow_delegation=False
)


def send_email(subject: str, body: str, to_addresses: Union[str, List[str]]):
    """Send an email using SMTP settings from environment.

    Returns a string with success or error message and prints to terminal.
    """
    if isinstance(to_addresses, str):
        recipients = [to_addresses]
    else:
        recipients = list(to_addresses)

    if not SMTP_HOST or not SMTP_PORT or not SMTP_USERNAME or not SMTP_PASSWORD or not SMTP_FROM:
        msg = (
            "SMTP not configured. Please set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, "
            "SMTP_PASSWORD, and SMTP_FROM in your .env"
        )
        print(msg)
        return msg

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_FROM
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject or ""

        msg.attach(MIMEText(body or "", "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, recipients, msg.as_string())

        success_msg = f"Email sent to: {', '.join(recipients)}"
        print(success_msg)
        return success_msg
    except Exception as exc:
        error_msg = f"Failed to send email: {exc}"
        print(error_msg)
        return error_msg


def format_email(subject: str, greeting: str, sections: List[tuple[str, str]], closing: str, signature_lines: List[str]) -> tuple[str, str]:
    """Build a standardized subject and plain-text body.

    sections: list of (title, content)
    signature_lines: e.g., ["Your Name", "Your Position", "Your Contact"]
    Returns (subject, body)
    """
    normalized_subject = subject.strip() if subject else ""
    lines: List[str] = []
    if greeting:
        lines.append(greeting.strip())
        lines.append("")
    for title, content in sections:
        title_line = title.strip() if title else ""
        if title_line:
            lines.append(f"{title_line}")
        if content:
            lines.append(content.strip())
        lines.append("")
    if closing:
        lines.append(closing.strip())
    if signature_lines:
        lines.append("")
        lines.extend([s.strip() for s in signature_lines if s.strip()])
    body = "\n".join(lines).strip() + "\n"
    return normalized_subject, body
