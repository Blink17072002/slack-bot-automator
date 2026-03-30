import requests
from bs4 import BeautifulSoup
import feedparser
import logging
from typing import Dict, Optional
from app.utils import normalize_text, parse_date
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def fetch_rss(url: str, etag: Optional[str] = None, last_modified: Optional[str] = None) -> Dict:
    """Fetches an RSS feed, utilizing ETag/Last-Modified caching if available."""
    logger.info(f"Fetching RSS: {url}")
    d = feedparser.parse(url, etag=etag, modified=last_modified)

    if hasattr(d, 'status') and d.status == 304:
        logger.info(f"Feed {url} unchanged (304 Not Modified).")
        return {'status': 304, 'items': [], 'etag': d.get('etag'), 'modified': d.get('modified')}

    items = []
    for entry in d.entries[:10]:
        items.append({
            'source_url': url,
            'title': entry.get('title', 'No Title'),
            'link': entry.get('link', url),
            'description': normalize_text(entry.get('summary', '') or entry.get('description', '')),
            'published_at': parse_date(entry.get('published', ''))
        })

    logger.info(f"RSS extracted {len(items)} items from {url}")
    return {'status': 200, 'items': items, 'etag': d.get('etag'), 'modified': d.get('modified')}


def fetch_html(url: str, etag: Optional[str] = None, last_modified: Optional[str] = None) -> Dict:
    """Fetches a generic HTML page and extracts articles using multiple strategies."""
    logger.info(f"Fetching HTML: {url}")

    req_headers = HEADERS.copy()
    if etag:
        req_headers['If-None-Match'] = etag
    if last_modified:
        req_headers['If-Modified-Since'] = last_modified
    
    try:
        response = requests.get(url, headers=req_headers, timeout=10)

        if response.status_code == 304:
            logger.info(f"HTML {url} unchanged (304 Not Modified).")
            return {'status': 304, 'items': [], 'etag': etag, 'modified': last_modified}
        
        response.raise_for_status()

        new_etag = response.headers.get('ETag')
        new_modified = response.headers.get('Last-Modified')

        soup = BeautifulSoup(response.content, 'html.parser')
        items = []
        parsed = urlparse(url)

        # Strategy 1: Look for <article> tags (most common on modern sites)
        articles = soup.find_all('article')
        if articles:
            logger.info(f"Using <article> tag strategy ({len(articles)} found)")
            for article in articles[:10]:
                heading = article.find(['h1', 'h2', 'h3', 'h4'])
                if not heading:
                    continue
                title = normalize_text(heading.get_text())
                if not title or len(title) < 5:
                    continue

                link_tag = article.find('a', href=True)
                link = link_tag['href'] if link_tag else url

                if link.startswith('/'):
                    link = f"{parsed.scheme}://{parsed.netloc}{link}"
                
                p_tag = article.find('p')
                description = normalize_text(p_tag.get_text()) if p_tag else "No description available."

                items.append({
                    'source_url': url,
                    'title': title,
                    'link': link,
                    'description': description,
                    'published_at': parse_date('')
                })

        # Strategy 2: Look for links within h2/h3 headings (common on blogs)
        if not items:
            logger.info("Failing back to h2/3 heading strategy")
            for heading in soup.find_all(['h2', 'h3']):
                link_tag = heading.find('a', href=True)
                if not link_tag:
                    continue
                title = normalize_text(heading.get_text())
                if not title or len(title) < 10:
                    continue
                
                link = link_tag['href']
                if link.startswith('/'):
                    link = f"{parsed.scheme}://{parsed.netloc}{link}"
                
                p_tag = heading.find_next_sibling('p')
                description = normalize_text(p_tag.get_text()) if p_tag else "No description available."

                items.append({
                    'source_url': url,
                    'title': title,
                    'link': link,
                    'description': description,
                    'published_at': parse_date('')
                })

        # Strategy 3: Look for any links with significant text
        if not items:
            logger.info("Falling back to generic link extraction strategy")
            seen_titles = set()
            for a_tag in soup.find_all('a', href=True):
                title = normalize_text(a_tag.get_text())
                if title and len(title) > 30 and title not in seen_titles:
                    seen_titles.add(title)
                    link = a_tag['href']
                    if link.startswith('/'):
                        link = f"{parsed.scheme}://{parsed.netloc}{link}"
                    items.append({
                        'source_url': url,
                        'title': title,
                        'link': link,
                        'description': 'No description available.',
                        'published_at': parse_date('')
                    })
                if len(items) >= 10:
                    break
        
        logger.info(f"HTML extracted {len(items)} items from {url}")
        return {'status': 200, 'items': items[:10], 'etag': new_etag, 'modified': new_modified}

    except Exception as e:
        logger.error(f"Error fetching HTML {url}: {e}")
        return {'status': 500, 'items': []}


def scrape_source(url: str, source_type: str, etag: Optional[str] = None, last_modified: Optional[str] = None) -> Dict:
    if source_type == 'rss' or '/feed' in url or url.endswith('.xml') or url.endswith('.rss'):
        return fetch_rss(url, etag, last_modified)
    else:
        return fetch_html(url, etag, last_modified)