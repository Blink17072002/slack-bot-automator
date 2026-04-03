import os
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("BOT_USER_TOKEN")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL")

DATABASE_URL = os.environ.get("DATABASE_URL") # postgres database
REDIS_URL = os.environ.get("REDIS_URL")
