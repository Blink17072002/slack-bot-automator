import logging
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.config import SLACK_BOT_TOKEN, SLACK_CHANNEL

logger = logging.getLogger(__name__)
client = WebClient(token=SLACK_BOT_TOKEN)

# Slack has a 3000 character limit per section block
SLACK_BLOCK_CHAR_LIMIT = 2900

def _chunk_text(text: str, max_len: int) -> list:
    """Splits text into chunks that fit within Slack's block character limit."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_idx = text.rfind('\n', 0, max_len)
        if split_idx == -1:
            split_idx = max_len
        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip('\n')
    return chunks


def post_digest(markdown_summary: str) -> bool:
    """Delivers the formatted digest to the configured Slack channel."""
    if not markdown_summary:
        logger.warning("Empty summary provided to Slack poster. Skipping.")
        return False

    logger.info(f"Posting digest to Slack channel: {SLACK_CHANNEL}")

    today = datetime.now().strftime("%A, %B %d, %Y")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📰 Daily Industry News Digest",
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"📅 {today}  •  Curated by your News Pipeline Bot"
                }
            ]
        },
        {"type": "divider"}
    ]

    text_chunks = _chunk_text(markdown_summary, SLACK_BLOCK_CHAR_LIMIT)
    for chunk in text_chunks:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": chunk
            }
        })

    # Footer
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "🤖 _Powered by Claude AI  •  Sources managed via Admin Dashboard_"
            }
        ]
    })

    try:
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=f"📰 Daily Industry News Digest — {today}",
            blocks=blocks,
            unfurl_links=False,
            unfurl_media=False
        )
        logger.info(f"Successfully posted to Slack! Message TS: {response['ts']}")
        return True
    except SlackApiError as e:
        logger.error(f"Error posting digest to Slack: {e.response['error']}")
        # Fallback: try posting as plain text without blocks
        try:
            logger.info("Attempting fallback: posting as plain text...")
            response = client.chat_postMessage(
                channel=SLACK_CHANNEL,
                text=f"📰 *Daily Industry News Digest - {today}*\n\n{markdown_summary}",
                unfurl_links=False
            )
            logger.info(f"Fallback post successful! Message TS: {response['ts']}")
            return True
        except SlackApiError as e2:
            logger.error(f"Fallback also failed: {e2.response['error']}")
            return False
