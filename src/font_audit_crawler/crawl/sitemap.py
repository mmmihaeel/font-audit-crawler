from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import httpx

from font_audit_crawler.crawl.http_fetch import fetch_bounded_text


def guess_sitemap_url(site_url: str) -> str:
    return urljoin(site_url, "/sitemap.xml")


def _extract_locations(xml_payload: str) -> list[str]:
    root = ET.fromstring(xml_payload)
    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}", 1)[0] + "}"

    if root.tag.endswith("sitemapindex"):
        return [
            node.text.strip()
            for node in root.findall(f"{namespace}sitemap/{namespace}loc")
            if node.text
        ]
    return [
        node.text.strip() for node in root.findall(f"{namespace}url/{namespace}loc") if node.text
    ]


def fetch_sitemap_urls(
    site_url: str,
    timeout: float = 10.0,
    max_bytes: int = 1_000_000,
) -> list[str]:
    sitemap_url = guess_sitemap_url(site_url)
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        try:
            response = fetch_bounded_text(client, sitemap_url, max_bytes=max_bytes)
        except httpx.HTTPError:
            return []
        if response is None:
            return []

        try:
            discovered = _extract_locations(response.text)
        except ET.ParseError:
            return []

        nested_urls: list[str] = []
        if discovered and all(url.endswith(".xml") for url in discovered):
            for nested_url in discovered:
                try:
                    nested_response = fetch_bounded_text(
                        client,
                        nested_url,
                        max_bytes=max_bytes,
                    )
                except httpx.HTTPError:
                    continue
                if nested_response is None:
                    continue
                try:
                    nested_urls.extend(_extract_locations(nested_response.text))
                except ET.ParseError:
                    continue
            return nested_urls
        return discovered
