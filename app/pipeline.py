import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.database import SessionLocal, engine, Base
from app.models import Source, PipelineRun
from app.scraper import scrape_source
from app.cache import get_source_cache_headers, set_source_cache_headers, deduplicate_items
from app.similarity import cluster_similar_items
from app.llm import generate_digest
from app.slack import post_digest


logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

MAX_WORKERS = 6


def _scrape_worker(source):
    """Thread worker for scraping a source."""
    try:
        etag, modified = get_source_cache_headers(source.url)

        result = scrape_source(
            source.url,
            source.source_type,
            etag,
            modified
        )

        return source, result

    except Exception as e:
        logger.exception(f"Worker failed for {source.url}")
        return source, {"status": 500, "items": []}


def execute_daily_pipeline() -> None:
    """Main ETL pipeline."""

    with SessionLocal() as db:

        run = PipelineRun(
            status="started",
            items_scanned=0,
            items_summarized=0
        )

        db.add(run)
        db.flush()

        logger.info(f"==== Starting Pipeline Run #{run.id} ====")

        try:

            active_sources = db.query(Source).filter(Source.is_active).all()

            if not active_sources:
                logger.warning("No active sources found.")
                run.status = "success"
                run.completed_at = datetime.now(timezone.utc)
                db.commit()
                return

            logger.info(f"Scraping {len(active_sources)} sources...")

            all_new_items = []

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

                futures = {
                    executor.submit(_scrape_worker, source): source
                    for source in active_sources
                }

                for future in as_completed(futures):

                    source, scrape_result = future.result()

                    if scrape_result.get("status") == 304:
                        logger.debug(f"{source.url} not modified.")
                        continue

                    if scrape_result.get("status") != 200:
                        logger.error(f"Scrape failed: {source.url}")
                        continue

                    items = scrape_result.get("items", [])

                    run.items_scanned += len(items)

                    new_items = deduplicate_items(items)

                    if new_items:
                        all_new_items.extend(new_items)

                    try:
                        set_source_cache_headers(
                            source.url,
                            scrape_result.get("etag"),
                            scrape_result.get("modified")
                        )
                    except Exception:
                        logger.exception("Failed saving cache headers")

            if not all_new_items:

                logger.info("No new articles discovered.")
                run.status = "success"

            else:

                logger.info(
                    f"{len(all_new_items)} new articles found. "
                    "Running semantic clustering..."
                )

                clustered_items = cluster_similar_items(all_new_items)

                logger.info(
                    f"Reduced {len(all_new_items)} → "
                    f"{len(clustered_items)} articles after clustering"
                )

                run.items_summarized = len(clustered_items)

                digest_markdown = generate_digest(clustered_items)

                if digest_markdown:

                    success = post_digest(digest_markdown)

                    if success:
                        run.status = "success"
                    else:
                        run.status = "failed_slack_post"
                        run.error_message = "Slack post failed"

                else:

                    run.status = "failed_llm"
                    run.error_message = "LLM failed to generate digest"

        except Exception as e:

            logger.exception("Pipeline fatal error")

            run.status = "failed_fatal"
            run.error_message = str(e)

        run.completed_at = datetime.now(timezone.utc)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        logger.info(f"==== Pipeline Run #{run.id} Complete ({run.status}) ====")


if __name__ == "__main__":
    execute_daily_pipeline()