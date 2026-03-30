import hashlib
import re
from datetime import datetime, timezone
import dateutil.parser


def generate_hash(url: str, title: str) -> str:
    """Generates a SHA-256 hash for exact deduplication matching."""
    content_string = f"{url}:{title}".encode('utf-8')
    return hashlib.sha256(content_string).hexdigest()


def normalize_text(html_text: str) -> str:
    """Removes excess whitespace from extracted text."""
    if not html_text:
        return ""

    # collapse multiple newlines and spaces
    clean_text = re.sub(r'\s+', ' ', html_text)
    return clean_text.strip()


def parse_date(date_string: str) -> datetime:
    """Attempts to canonicalize a date string into an aware UTC datetime."""
    if not date_string:
        return datetime.now(timezone.utc)
    try:
        dt = dateutil.parser.parse(date_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)