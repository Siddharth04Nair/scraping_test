"""
Scraper Helper - Web crawling using Crawl4AI
"""

from typing import List, Dict, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
import re
from urllib.parse import urlparse
from helpers.loggerHelper import get_logger

logger = get_logger(__name__)


async def deep_crawl_website(
    url: str, max_depth: Optional[int] = 2, max_pages: Optional[int] = 20
) -> List[Dict[str, str]]:
    """
    Deep crawl a website and extract clean content from all pages.

    Args:
        url: Base URL to start crawling from
        max_depth: Maximum depth to crawl (None for unlimited, default: 2)
        max_pages: Maximum number of pages to crawl (default: 20)

    Returns:
        List of dictionaries with 'url' and 'content' keys

    Raises:
        ValueError: If URL is invalid
        Exception: If crawling fails
    """
    # Validate URL
    if not _is_valid_url(url):
        raise ValueError(f"Invalid URL: {url}")

    logger.info(f"Starting deep crawl of {url} (max_depth={max_depth}, max_pages={max_pages})")

    try:
        # Configure deep crawl strategy
        deep_crawl_config = BFSDeepCrawlStrategy(
            max_depth=max_depth if max_depth is not None else 999,
            include_external=False,  # Stay within same domain
        )

        # Configure browser
        browser_config = BrowserConfig(
            enable_stealth=True,
            headless=False,
        )

        # Configure crawler
        crawler_config = CrawlerRunConfig(
            deep_crawl_strategy=deep_crawl_config,
            verbose=False,
            only_text=True,
            word_count_threshold=10,  # Skip pages with very little content
            excluded_tags=["nav", "footer", "header", "script", "style", "noscript"],
            remove_overlay_elements=True,
        )

        # Perform crawl
        async with AsyncWebCrawler(config=browser_config) as crawler:
            results = await crawler.arun(url, config=crawler_config)

        # Process results
        pages_data = []
        page_count = 0

        # Handle both single result and list of results
        results_list = results if isinstance(results, list) else [results]

        for result in results_list:
            # Check max pages limit
            if max_pages and page_count >= max_pages:
                logger.info(f"Reached max_pages limit of {max_pages}")
                break

            # Skip failed crawls
            if not result.success:
                logger.warning(f"Failed to crawl: {result.url}")
                continue

            # Skip non-content pages
            if _should_skip_url(result.url):
                logger.debug(f"Skipping non-content URL: {result.url}")
                continue

            # Extract clean content (prefer markdown)
            content = result.markdown if result.markdown else result.cleaned_html
            if not content or len(content.strip()) < 100:
                logger.debug(f"Skipping page with insufficient content: {result.url}")
                continue

            pages_data.append({"url": result.url, "content": content})
            page_count += 1
            logger.info(f"Extracted content from: {result.url} ({len(content)} chars)")

        logger.info(f"Successfully crawled {len(pages_data)} pages")
        return pages_data

    except Exception as e:
        logger.error(f"Error during crawling: {e}", exc_info=True)
        raise


def _is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.

    Args:
        url: URL string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def _should_skip_url(url: str) -> bool:
    """
    Check if a URL should be skipped based on pattern.

    Args:
        url: URL to check

    Returns:
        True if should skip, False otherwise
    """
    url_lower = url.lower()

    # Skip common non-content patterns
    skip_patterns = [
        "/feed/",
        "/rss/",
        "/atom/",
        "robots.txt",
        "sitemap.xml",
        "/wp-json/",
        "/api/",
        "/download/",
    ]

    for pattern in skip_patterns:
        if pattern in url_lower:
            return True

    return False

