from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path

import pytest

from font_audit_crawler.models.config_models import (
    AppConfig,
    ScreenshotMode,
    SitemapMode,
    ViewportMode,
)
from font_audit_crawler.scanner import run_scan


@pytest.mark.parametrize(
    ("site_name", "expected_types"),
    [
        ("approved-only", set()),
        ("overlay-cookie-banner", set()),
        ("bad-local-font-face", {"local_css_font_face", "local_font_asset_loaded"}),
        ("suspicious-fallback-stack", {"suspicious_fallback_stack"}),
        (
            "non-approved-legacy-font",
            {"runtime_non_approved_font", "suspicious_fallback_stack"},
        ),
        (
            "inline-style-issue",
            {
                "runtime_non_approved_font",
                "suspicious_fallback_stack",
                "inline_font_declaration",
            },
        ),
        ("vendor-widget-exception", {"vendor_exception"}),
        ("locale-fallback-review", {"locale_fallback_review"}),
    ],
)
def test_runtime_scan_detects_fixture_site_findings(
    fixture_server: Callable[[str], AbstractContextManager[str]],
    tmp_path: Path,
    site_name: str,
    expected_types: set[str],
) -> None:
    config = AppConfig()
    config.scan.max_pages = 3
    config.scan.viewport = ViewportMode.DESKTOP
    config.scan.screenshot = ScreenshotMode.NONE
    config.scan.sitemap = SitemapMode.NEVER

    with fixture_server(site_name) as base_url:
        report = asyncio.run(run_scan(start_url=base_url, config=config, output_dir=tmp_path))

    finding_types = {finding.type.value for finding in report.findings}
    assert finding_types == expected_types


def test_sitemap_and_same_origin_crawl_are_respected(
    fixture_server: Callable[[str], AbstractContextManager[str]],
    tmp_path: Path,
) -> None:
    config = AppConfig()
    config.scan.max_pages = 20
    config.scan.max_depth = 2
    config.scan.screenshot = ScreenshotMode.NONE
    config.scan.viewport = ViewportMode.DESKTOP
    config.scan.sitemap = SitemapMode.AUTO

    with fixture_server("full-site") as base_url:
        report = asyncio.run(run_scan(start_url=base_url, config=config, output_dir=tmp_path))

    assert len(report.scanned_urls) >= 6
    assert any("/non-approved-legacy.html" in url for url in report.scanned_urls)
    assert any("/inline-style.html" in url for url in report.scanned_urls)
    assert any(finding.type.value == "local_font_asset_loaded" for finding in report.findings)
