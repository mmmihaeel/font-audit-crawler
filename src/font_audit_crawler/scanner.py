from __future__ import annotations

from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from font_audit_crawler.audit.rules_engine import classify_page
from font_audit_crawler.browser.page_loader import capture_page_screenshot, open_page_snapshot
from font_audit_crawler.browser.session import browser_session
from font_audit_crawler.config import load_rules_bundle
from font_audit_crawler.crawl.crawler import discover_urls
from font_audit_crawler.models.config_models import AppConfig, ScreenshotMode, ViewportMode
from font_audit_crawler.models.findings import Finding, FindingType
from font_audit_crawler.models.reports import (
    CrawlSummary,
    FamilyReplacementSummary,
    HeadRequirements,
    PageReport,
    SiteReport,
)
from font_audit_crawler.models.rules import RulesBundle
from font_audit_crawler.utils.fonts import (
    approved_fonts_google_snippet,
    dedupe_preserve_order,
    primary_font,
)
from font_audit_crawler.utils.paths import relative_to


def resolve_viewports(viewport_mode: ViewportMode) -> list[str]:
    if viewport_mode is ViewportMode.BOTH:
        return [ViewportMode.DESKTOP.value, ViewportMode.MOBILE.value]
    return [viewport_mode.value]


def build_head_requirements(
    report_pages: list[PageReport],
    findings: list[Finding],
    rules: RulesBundle,
) -> HeadRequirements:
    required_families: list[str] = []
    for page in report_pages:
        required_families.extend(
            family for family in page.observed_primary_fonts if rules.is_approved(family)
        )
    for finding in findings:
        if finding.recommended is not None:
            required_families.append(finding.recommended.family)

    deduped = dedupe_preserve_order(required_families)
    google_hosted_families: list[str] = []
    non_google_families: list[str] = []
    approved_models = []
    for family_name in deduped:
        approved_family = rules.approved_family(family_name)
        if approved_family is None:
            continue
        approved_models.append(approved_family)
        if approved_family.google_hosted:
            google_hosted_families.append(approved_family.name)
        else:
            non_google_families.append(approved_family.name)

    notes: list[str] = []
    if non_google_families:
        for family_name in non_google_families:
            notes.append(
                f"{family_name} is approved but not assumed to be Google-hosted; load it from "
                "the approved site-owned or licensed source outside CSS."
            )

    return HeadRequirements(
        required_families=deduped,
        google_hosted_families=google_hosted_families,
        non_google_families=non_google_families,
        google_fonts_snippet=approved_fonts_google_snippet(
            [family for family in approved_models if family.google_hosted]
        ),
        notes=notes,
    )


def build_recommended_replacements(findings: list[Finding]) -> list[FamilyReplacementSummary]:
    counts: Counter[tuple[str, str]] = Counter()
    for finding in findings:
        if (
            finding.type is FindingType.RUNTIME_NON_APPROVED_FONT
            and finding.primary_font
            and finding.recommended is not None
            and finding.primary_font != finding.recommended.family
        ):
            counts[(finding.primary_font, finding.recommended.family)] += int(
                finding.evidence.get("occurrences", 1)
            )
    return [
        FamilyReplacementSummary(
            detected_family=detected_family,
            recommended_family=recommended_family,
            occurrences=occurrences,
        )
        for (detected_family, recommended_family), occurrences in sorted(counts.items())
    ]


async def run_scan(
    *,
    start_url: str,
    config: AppConfig,
    output_dir: Path,
) -> SiteReport:
    rules = load_rules_bundle(config.rules_path)
    crawl_result = discover_urls(
        start_url,
        max_pages=config.scan.max_pages,
        max_depth=config.scan.max_depth,
        include=config.scan.include,
        exclude=config.scan.exclude,
        timeout=config.scan.timeout_ms / 1000,
        sitemap_mode=config.scan.sitemap,
        keep_query_strings=config.scan.keep_query_strings,
    )
    if not crawl_result.urls:
        raise RuntimeError("No crawlable same-origin pages were discovered.")

    pages: list[PageReport] = []
    findings: list[Finding] = []

    async with browser_session() as browser:
        for url in crawl_result.urls:
            for viewport in resolve_viewports(config.scan.viewport):
                async with open_page_snapshot(
                    browser,
                    url,
                    viewport_name=viewport,
                    timeout_ms=config.scan.timeout_ms,
                    wait_after_load_ms=config.scan.wait_after_load_ms,
                    max_elements_per_page=config.scan.max_elements_per_page,
                ) as loaded_page:
                    page_findings = classify_page(loaded_page.snapshot, rules)

                    screenshot_path: Path | None = None
                    should_capture = config.scan.screenshot is ScreenshotMode.PAGE or (
                        config.scan.screenshot is ScreenshotMode.FINDING and bool(page_findings)
                    )
                    if should_capture and loaded_page.snapshot.page_error is None:
                        url_path = urlparse(url).path.rstrip("/")
                        page_slug = Path(url_path).name or "index"
                        screenshot_path = (
                            output_dir
                            / "screenshots"
                            / f"{len(pages):03d}-{viewport}-{page_slug}.png"
                        )
                        await capture_page_screenshot(loaded_page.page, screenshot_path)

                    relative_screenshot = relative_to(output_dir, screenshot_path)
                    for finding in page_findings:
                        finding.screenshot_path = relative_screenshot
                    findings.extend(page_findings)

                    pages.append(
                        PageReport(
                            url=loaded_page.snapshot.url,
                            viewport=loaded_page.snapshot.viewport,
                            visible_text_elements=len(loaded_page.snapshot.elements),
                            font_face_rules=len(loaded_page.snapshot.font_face_rules),
                            font_requests=len(loaded_page.snapshot.font_requests),
                            findings_total=len(page_findings),
                            screenshot_path=relative_screenshot,
                            page_error=loaded_page.snapshot.page_error,
                            observed_primary_fonts=dedupe_preserve_order(
                                [
                                    font
                                    for element in loaded_page.snapshot.elements
                                    if (font := primary_font(element.font_family)) is not None
                                ]
                            ),
                            font_request_urls=sorted(
                                {request.url for request in loaded_page.snapshot.font_requests}
                            ),
                            font_face_families=dedupe_preserve_order(
                                [
                                    font_face.font_family
                                    for font_face in loaded_page.snapshot.font_face_rules
                                ]
                            ),
                        )
                    )

    head_requirements = build_head_requirements(pages, findings, rules)
    recommended_replacements = build_recommended_replacements(findings)
    return SiteReport.build(
        site=start_url,
        start_url=crawl_result.start_url,
        scanned_urls=crawl_result.urls,
        crawl=CrawlSummary(
            start_url=crawl_result.start_url,
            discovered_urls=crawl_result.urls,
            sitemap_urls=crawl_result.sitemap_urls,
        ),
        pages=pages,
        findings=findings,
        recommended_replacements=recommended_replacements,
        head_requirements=head_requirements,
    )
