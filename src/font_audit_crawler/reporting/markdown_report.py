from __future__ import annotations

from pathlib import Path

from font_audit_crawler.models.reports import SiteReport


def write_markdown_report(path: Path, report: SiteReport) -> None:
    lines: list[str] = [
        f"# Font Audit Report: {report.site}",
        "",
        "## Summary",
        "",
        f"- Generated at: `{report.generated_at}`",
        f"- Scanned pages: `{report.summary.scanned_pages}`",
        f"- Successful pages: `{report.summary.successful_pages}`",
        f"- Pages with load errors: `{report.summary.errored_pages}`",
        f"- Total findings: `{report.summary.findings_total}`",
        f"- Findings by severity: `{report.summary.findings_by_severity}`",
        f"- Findings by type: `{report.summary.findings_by_type}`",
        "",
        "## Head Requirements",
        "",
        f"- Required approved families: `{report.head_requirements.required_families}`",
        f"- Google-hosted approved families: `{report.head_requirements.google_hosted_families}`",
        f"- Non-Google approved families: `{report.head_requirements.non_google_families}`",
    ]
    if report.head_requirements.google_fonts_snippet:
        lines.extend(
            [
                "",
                "### Google Fonts Snippet",
                "",
                "```html",
                report.head_requirements.google_fonts_snippet,
                "```",
            ]
        )
    if report.head_requirements.notes:
        lines.extend(["", "### Head Notes", ""])
        lines.extend(f"- {note}" for note in report.head_requirements.notes)

    lines.extend(["", "## Recommended Replacements", ""])
    if report.recommended_replacements:
        lines.append("| Detected family | Recommended family | Occurrences |")
        lines.append("| --- | --- | ---: |")
        for replacement in report.recommended_replacements:
            lines.append(
                f"| `{replacement.detected_family}` | `{replacement.recommended_family}` | "
                f"{replacement.occurrences} |"
            )
    else:
        lines.append("No non-approved runtime font families were detected.")

    lines.extend(["", "## Unresolved Non-CSS Issues", ""])
    if report.unresolved_non_css_findings:
        for finding in report.unresolved_non_css_findings:
            lines.append(
                f"- `{finding.type.value}` on `{finding.url}`"
                + (f" (`{finding.selector}`)" if finding.selector else "")
            )
    else:
        lines.append("No inline or local font-loading issues were detected at runtime.")

    lines.extend(["", "## Manual Review Buckets", ""])
    if report.manual_review_findings:
        for finding in report.manual_review_findings:
            lines.append(
                f"- `{finding.type.value}` on `{finding.url}`"
                + (f" (`{finding.selector}`)" if finding.selector else "")
            )
    else:
        lines.append("No vendor or locale-specific manual-review buckets were detected.")

    lines.extend(["", "## Pages", ""])
    lines.append("| URL | Viewport | Visible text | Findings | Screenshot |")
    lines.append("| --- | --- | ---: | ---: | --- |")
    for page in report.pages:
        lines.append(
            f"| `{page.url}` | `{page.viewport}` | {page.visible_text_elements} | "
            f"{page.findings_total} | `{page.screenshot_path or '-'}` |"
        )

    lines.extend(["", "## Findings", ""])
    if not report.findings:
        lines.append("No findings.")
    for finding in report.findings:
        lines.extend(
            [
                f"### {finding.type.value}",
                f"- Severity: `{finding.severity.value}`",
                f"- URL: `{finding.url}`",
                f"- Viewport: `{finding.viewport}`",
            ]
        )
        if finding.selector:
            lines.append(f"- Selector: `{finding.selector}`")
        if finding.text_sample:
            lines.append(f"- Text: `{finding.text_sample}`")
        if finding.font_stack:
            lines.append(f"- Runtime stack: `{finding.font_stack}`")
        if finding.primary_font:
            lines.append(f"- Primary font: `{finding.primary_font}`")
        if finding.recommended:
            lines.append(f"- Recommended family: `{finding.recommended.family}`")
            lines.append(f"- Recommended stack: `{finding.recommended.css_stack}`")
            lines.append(
                "- Preserve weight/style: "
                f"`{finding.recommended.font_weight}` / `{finding.recommended.font_style}`"
            )
        if finding.note:
            lines.append(f"- Note: {finding.note}")
        occurrences = finding.evidence.get("occurrences")
        if occurrences:
            lines.append(f"- Occurrences: `{occurrences}`")
        sample_selectors = finding.evidence.get("sample_selectors")
        if sample_selectors:
            lines.append(f"- Sample selectors: `{sample_selectors}`")
        sample_texts = finding.evidence.get("sample_texts")
        if sample_texts:
            lines.append(f"- Sample texts: `{sample_texts}`")
        if finding.screenshot_path:
            lines.append(f"- Screenshot: `{finding.screenshot_path}`")
        if finding.evidence:
            lines.append(f"- Evidence: `{finding.evidence}`")
        lines.append("")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
