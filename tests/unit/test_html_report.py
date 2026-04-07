from __future__ import annotations

from pathlib import Path

from font_audit_crawler.models.findings import Finding, FindingType, Severity
from font_audit_crawler.models.reports import CrawlSummary, HeadRequirements, PageReport, SiteReport
from font_audit_crawler.reporting.html_report import write_html_report


def test_html_report_escapes_runtime_content_and_includes_csp(tmp_path: Path) -> None:
    report = SiteReport.build(
        site="https://example.com",
        start_url="https://example.com",
        scanned_urls=["https://example.com"],
        crawl=CrawlSummary(
            start_url="https://example.com",
            discovered_urls=["https://example.com"],
        ),
        pages=[
            PageReport(
                url="https://example.com",
                viewport="desktop",
                visible_text_elements=1,
                font_face_rules=0,
                font_requests=0,
                findings_total=1,
            )
        ],
        findings=[
            Finding(
                id="finding-1",
                type=FindingType.RUNTIME_NON_APPROVED_FONT,
                severity=Severity.HIGH,
                url="https://example.com",
                viewport="desktop",
                text_sample="<script>alert(1)</script>",
                font_stack="Arial",
                primary_font="Arial",
                note="Unsafe sample",
            )
        ],
        recommended_replacements=[],
        head_requirements=HeadRequirements(required_families=["Roboto"]),
    )
    output = tmp_path / "report.html"
    write_html_report(output, report)
    html = output.read_text(encoding="utf-8")

    assert "Content-Security-Policy" in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
