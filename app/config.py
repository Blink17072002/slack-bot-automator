import os
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("BOT_USER_TOKEN")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL")

DATABASE_URL = os.environ.get("DATABASE_URL") # postgres database
REDIS_URL = os.environ.get("REDIS_URL")

# Scheduler: Run by 8:00am every day
CRON_HOUR = int(os.environ.get("CRON_HOUR", "8"))
CRON_MINUTE = int(os.environ.get("CRON MINUTE", "0"))