from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import httpx


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


def fetch_sitemap_urls(site_url: str, timeout: float = 10.0) -> list[str]:
    sitemap_url = guess_sitemap_url(site_url)
    try:
        response = httpx.get(sitemap_url, timeout=timeout, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError:
        return []

    try:
        discovered = _extract_locations(response.text)
    except ET.ParseError:
        return []
    nested_urls: list[str] = []
    if discovered and all(url.endswith(".xml") for url in discovered):
        for nested_url in discovered:
            try:
                nested_response = httpx.get(nested_url, timeout=timeout, follow_redirects=True)
                nested_response.raise_for_status()
                nested_urls.extend(_extract_locations(nested_response.text))
            except (httpx.HTTPError, ET.ParseError):
                continue
        return nested_urls
    return discovered
