import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API key (from your .env file)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME or "")