from __future__ import annotations

from collections import deque

import httpx
from selectolax.parser import HTMLParser

from font_audit_crawler.constants import DEFAULT_USER_AGENT
from font_audit_crawler.crawl.http_fetch import fetch_bounded_text
from font_audit_crawler.crawl.normalization import is_same_origin, normalize_url
from font_audit_crawler.crawl.sitemap import fetch_sitemap_urls
from font_audit_crawler.crawl.url_filters import should_visit
from font_audit_crawler.models.config_models import SitemapMode
from font_audit_crawler.models.crawl import CrawlResult


def discover_urls(
    start_url: str,
    *,
    max_pages: int,
    max_depth: int,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    timeout: float = 10.0,
    sitemap_mode: SitemapMode = SitemapMode.AUTO,
    keep_query_strings: bool = False,
    max_page_bytes: int = 2_000_000,
    max_sitemap_bytes: int = 1_000_000,
) -> CrawlResult:
    include = include or []
    exclude = exclude or []

    normalized_start = normalize_url(start_url, keep_query_strings=keep_query_strings)
    if normalized_start is None:
        raise ValueError(f"Unsupported start URL: {start_url}")

    discovered: list[str] = []
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(normalized_start, 0)])
    sitemap_urls: list[str] = []

    if sitemap_mode is not SitemapMode.NEVER:
        for sitemap_url in fetch_sitemap_urls(
            normalized_start,
            timeout=timeout,
            max_bytes=max_sitemap_bytes,
        ):
            normalized = normalize_url(
                sitemap_url,
                keep_query_strings=keep_query_strings,
            )
            if normalized and is_same_origin(normalized, normalized_start):
                sitemap_urls.append(normalized)
        for sitemap_url in sitemap_urls:
            queue.append((sitemap_url, 1))

    headers = {"User-Agent": DEFAULT_USER_AGENT}
    with httpx.Client(headers=headers, follow_redirects=True, timeout=timeout) as client:
        while queue and len(discovered) < max_pages:
            current, depth = queue.popleft()
            if current in visited or depth > max_depth:
                continue
            if not should_visit(current, include, exclude):
                continue

            visited.add(current)
            try:
                response = fetch_bounded_text(
                    client,
                    current,
                    max_bytes=max_page_bytes,
                )
            except httpx.HTTPError:
                continue
            if response is None:
                continue

            if not any(
                content_type in response.content_type
                for content_type in ("text/html", "application/xhtml+xml")
            ):
                continue

            discovered.append(current)
            if depth >= max_depth:
                continue

            parser = HTMLParser(response.text)
            href_candidates: set[str] = set()
            for node in parser.css("a[href]"):
                href = node.attributes.get("href")
                if href:
                    href_candidates.add(href)
            hrefs = sorted(href_candidates)
            for href in hrefs:
                candidate = normalize_url(
                    href,
                    current,
                    keep_query_strings=keep_query_strings,
                )
                if (
                    candidate
                    and is_same_origin(candidate, normalized_start)
                    and candidate not in visited
                ):
                    queue.append((candidate, depth + 1))

    unique_urls = []
    seen_urls: set[str] = set()
    for url in discovered:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_urls.append(url)

    return CrawlResult(
        start_url=normalized_start,
        urls=unique_urls[:max_pages],
        sitemap_urls=sorted(set(sitemap_urls)),
    )
