import logging
from typing import List, Dict, Optional, Tuple
from app.redis_client import RedisSession
from app.utils import generate_hash

logger = logging.getLogger(__name__)


# Redis key prefixes
HASH_PREFIX = "news_hash:"
ETAG_PREFIX = "source_etag:"
MODIFIED_PREFIX = "source_modified:"

# Expire hashes after 7 days
CACHE_TTL = 60 * 60 * 24 * 7


def get_source_cache_headers(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Retrieves cached ETag and Last-Modified headers for a source URL."""
    with RedisSession() as redis_db:
        etag = redis_db.get(f"{ETAG_PREFIX}{url}")
        modified = redis_db.get(f"{MODIFIED_PREFIX}{url}")

    return etag, modified


def set_source_cache_headers(url: str, etag: Optional[str], modified: Optional[str]) -> None:
    """Stores ETag and Last-Modified headers for a source URL."""
    with RedisSession() as redis_db:
        pipe = redis_db.pipeline()
        
        if etag:
            pipe.set(f"{ETAG_PREFIX}{url}", etag)
        if modified:
            pipe.set(f"{MODIFIED_PREFIX}{url}", modified)

        pipe.execute()

    
def deduplicate_items(items: List[Dict]) -> List[Dict]:
    """Deduplicate scraped items using Redis"""
    if not items:
        return []

    keys = []
    valid_items = []

    for item in items:
        link = item.get("link")
        title = item.get("title", "")

        if not link:
            logger.warning("Skipping item without link")
            continue

        item_hash = generate_hash(link, title)
        redis_key = f"{HASH_PREFIX}{item_hash}"

        keys.append(redis_key)
        valid_items.append(item)

    if not keys:
        return []

    with RedisSession() as redis_db:
        existing = redis_db.mget(keys)

        new_items = []
        pipe = redis_db.pipeline()

        for item, key, exists in zip(valid_items, keys, existing):
            if exists is None:
                pipe.setex(key, CACHE_TTL, "1")
                new_items.append(item)

                logger.debug(f"New item discovered: {item.get('title')}")

        if new_items:
            pipe.execute()

    logger.info(f"Deduplication complete. {len(items)} scanned, {len(new_items)} new.")

    return new_items
