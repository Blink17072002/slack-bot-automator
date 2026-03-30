import logging
from typing import List, Dict, Optional
import anthropic
from app.config import CLAUDE_API_KEY

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def generate_digest(items: List[Dict]) -> Optional[str]:
    if not items:
        logger.info("No items provided to summarize.")
        return None

    logger.info(f"Sending {len(items)} items to Claude 3 Haiku for summarization.")

    content_blocks = []
    for i, item in enumerate(items, 1):
        content_blocks.append(f"[{i}] Title: {item['title']}\nDescription: {item['description']}\nLink: {item['link']}")

    compiled_text = "\n\n".join(content_blocks)

    prompt = f"""
        You are an expert industry and technology analyst.
        Below is a list of NEW, recently published articles extracted from various industry sources.

        Please read the titles and descriptions and synthesize them into a professional, concise daily digest.

        CRITICAL - You MUST format the output using Slack's mrkdwn syntax (NOT standard markdown):
        - Bold text uses single asterisks: *bold text*
        - Links use angle brackets: <https://example.com|Link Text>
        - Use bullet points with • (the bullet character, not dashes)
        - Use blank lines betwen sections for spacing
        - Section headers should be bold with an emoji prefix, e.g. *🤖 AI & Automation*

        Structure rules:
        - Group articles into 3-5 themed sections
        - Each article should be one bullet with a bold linked title and a one-sentence summary
        - Format each article like: • <url|*Article Title*> - One sentence summary.
        - Keep the tone objective, informative, and concise
        - End with a short one-liner sign-off like "_That's today's digest. Stay informed!_"

        Here is the content:
        {compiled_text}
    """

    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1500,
            temperature=0.0,
            system="You are an expert industry analyst creating a daily digest for Slack. You MUST use Slack mrkdwn formatting, NOT standard markdown.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        # return message.content[0].text
        return "".join(block.text for block in message.content if hasattr(block, "text"))
    except Exception as e:
        logger.error(f"Error generating summary with Claude: {e}")
        return None