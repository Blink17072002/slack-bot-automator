# Daily News Digest Bot

## 📖 What does this do?
This application is an automated news aggregation and delivery pipeline. It continuously monitors and scrapes designated websites and RSS feeds (such as TechCrunch's AI category) to extract the latest news articles. Using Anthropic's Claude 3 API, it translates the raw scraped data into a concise, professional daily digest. Finally, it formats this digest and automatically publishes it to a predefined Slack channel at a scheduled time. Additionally, it offers a secure FastAPI admin dashboard where users can manually trigger pipeline runs, view recent pipeline executions, and manage the news sources.

## 💻 What tech did I use?
* **Backend Framework:** FastAPI (Python) - For building the API and admin dashboard.
* **Database / ORM:** SQLAlchemy with PostgreSQL (via `pg8000`) - For storing sources and tracking pipeline runs.
* **Caching & Storage:** Redis - To cache temporary scraping payload and track operations.
* **Task Scheduling:** APScheduler - For running daily automated tasks in the background.
* **Web Scraping:** BeautifulSoup4 & FeedParser - To effectively extract unstructured titles and descriptions from webpages and RSS feeds.
* **AI Integration:** Anthropic Claude 3 (`claude-3-haiku-20240307`) - For fast, intelligent, and context-aware information summarization.
* **Communication:** Slack SDK - For authenticating and sending formatted message blocks directly to Slack channels.
* **Templating:** Jinja2 - For rendering the web admin UI.

## 🚀 What business problem does this solve?
**Information Overload & Team Alignment.**

In fast-paced industries (like Artificial Intelligence and Tech), staying up to date with the latest trends takes significant time. Professionals often spend hours browsing disjointed news sources or miss out on critical updates. This bot solves that by acting as a virtual researcher:
1. It distills large volumes of noisy data into actionable, succinct insights.
2. It brings the information directly into the team's primary communication hub (Slack), minimizing context switching.
3. It guarantees the entire team receives curated, high-quality intel every day, fostering better strategic alignment and awareness with exactly zero manual effort.

## 🛠️ Local Development Setup

### 1. Prerequisites
Ensure you have Python 3.9+ installed and a PostgreSQL/Redis instance available.

### 2. Installation
```bash
# Clone the repository and change directory
cd slack_bot_automator

# Create and activate a virtual environment
python -m venv virtual
# On Windows:
virtual\Scripts\activate
# On Mac/Linux:
source virtual/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory (alongside `bot.py`) and populate it with the appropriate credentials:
```env
BOT_USER_TOKEN=xoxb-your-slack-bot-token
CLAUDE_API_KEY=sk-ant-your-anthropic-key
SLACK_CHANNEL=C1234567890
# Add your REDIS_URL and DATABASE_URL if configured in your environment
```

### 4. Running the Application
**Run the Admin Dashboard & Scheduler:**
```bash
uvicorn app.main:app --reload
```
The fastAPI application will boot up at `http://localhost:8000`. The BackgroundScheduler will automatically attach itself to the FastAPI lifecycle and trigger the digest daily.

**Alternatively, to run the standalone bot script immediately:**
```bash
python bot.py
```
