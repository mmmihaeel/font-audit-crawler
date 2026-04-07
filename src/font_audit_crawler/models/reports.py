from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from font_audit_crawler import __version__
from font_audit_crawler.models.findings import Finding


class CrawlSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_url: str
    discovered_urls: list[str]
    sitemap_urls: list[str] = Field(default_factory=list)


class PageReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    viewport: str
    visible_text_elements: int
    font_face_rules: int
    font_requests: int
    findings_total: int
    screenshot_path: str | None = None
    page_error: str | None = None
    observed_primary_fonts: list[str] = Field(default_factory=list)
    font_request_urls: list[str] = Field(default_factory=list)
    font_face_families: list[str] = Field(default_factory=list)


class FamilyReplacementSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detected_family: str
    recommended_family: str
    occurrences: int


class HeadRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_families: list[str] = Field(default_factory=list)
    google_hosted_families: list[str] = Field(default_factory=list)
    non_google_families: list[str] = Field(default_factory=list)
    google_fonts_snippet: str | None = None
    notes: list[str] = Field(default_factory=list)


class ScanSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scanned_pages: int
    successful_pages: int
    errored_pages: int
    findings_total: int
    findings_by_severity: dict[str, int]
    findings_by_type: dict[str, int]
    urls_with_findings: list[str] = Field(default_factory=list)


class SiteReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_version: str = __version__
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    site: str
    start_url: str
    scanned_urls: list[str]
    crawl: CrawlSummary
    pages: list[PageReport]
    findings: list[Finding] = Field(default_factory=list)
    summary: ScanSummary
    recommended_replacements: list[FamilyReplacementSummary] = Field(default_factory=list)
    head_requirements: HeadRequirements = Field(default_factory=HeadRequirements)
    manual_review_findings: list[Finding] = Field(default_factory=list)
    unresolved_non_css_findings: list[Finding] = Field(default_factory=list)

    @classmethod
    def build(
        cls,
        *,
        site: str,
        start_url: str,
        scanned_urls: list[str],
        crawl: CrawlSummary,
        pages: list[PageReport],
        findings: list[Finding],
        recommended_replacements: list[FamilyReplacementSummary],
        head_requirements: HeadRequirements,
    ) -> SiteReport:
        severity_counts = Counter(finding.severity.value for finding in findings)
        type_counts = Counter(finding.type.value for finding in findings)
        urls_with_findings = sorted({finding.url for finding in findings})
        page_errors = sum(1 for page in pages if page.page_error)
        summary = ScanSummary(
            scanned_pages=len(pages),
            successful_pages=len(pages) - page_errors,
            errored_pages=page_errors,
            findings_total=len(findings),
            findings_by_severity=dict(sorted(severity_counts.items())),
            findings_by_type=dict(sorted(type_counts.items())),
            urls_with_findings=urls_with_findings,
        )
        manual_review_findings = [
            finding for finding in findings if finding.severity.value == "manual_review"
        ]
        unresolved_non_css_findings = [
            finding
            for finding in findings
            if finding.type.value
            in {"inline_font_declaration", "local_font_asset_loaded", "local_css_font_face"}
        ]
        return cls(
            site=site,
            start_url=start_url,
            scanned_urls=scanned_urls,
            crawl=crawl,
            pages=pages,
            findings=findings,
            summary=summary,
            recommended_replacements=recommended_replacements,
            head_requirements=head_requirements,
            manual_review_findings=manual_review_findings,
            unresolved_non_css_findings=unresolved_non_css_findings,
        )
