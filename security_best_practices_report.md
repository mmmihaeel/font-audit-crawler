# Security Best Practices Report

## Executive summary

No open critical or high-severity implementation flaws were found after this hardening pass. The codebase now follows a solid secure-by-default posture for an operator-run CLI that scans third-party websites, with the remaining risks concentrated in operational deployment rather than code defects.

## Resolved findings

### SEC-001 Medium: bounded fetch limits were needed for crawl and sitemap discovery

Impact: Without response-size caps, a hostile or misconfigured target could force the crawler to load excessive HTML or XML into memory during discovery.

Status: Fixed.

Evidence:

- `src/font_audit_crawler/crawl/http_fetch.py:14`
- `src/font_audit_crawler/crawl/crawler.py:17`
- `src/font_audit_crawler/crawl/sitemap.py:32`
- `src/font_audit_crawler/models/config_models.py:35`

Resolution:

- Added bounded streaming fetch logic for text responses.
- Enforced size caps for both HTML discovery and sitemap parsing.
- Added typed config defaults for `max_page_bytes` and `max_sitemap_bytes`.

### SEC-002 Medium: HTML report rendering needed explicit template hardening

Impact: The HTML report contains captured runtime text from scanned pages, so broken autoescaping or permissive browser behavior could allow unsafe content rendering.

Status: Fixed.

Evidence:

- `src/font_audit_crawler/reporting/html_report.py:11`
- `src/font_audit_crawler/reporting/templates/report.html.j2:4`

Resolution:

- Enforced Jinja `StrictUndefined`.
- Corrected autoescaping coverage for `.html.j2` templates.
- Added a restrictive Content Security Policy and `referrer` suppression to the generated HTML report.

### SEC-003 Medium: consent-management UI needed to be excluded from audit evidence

Impact: Cookie banners and consent controls are third-party chrome, not site typography. If included, they can create false positives and mislead remediation decisions.

Status: Fixed.

Evidence:

- `src/font_audit_crawler/browser/page_loader.py:34`
- `src/font_audit_crawler/extract/text_nodes.py:35`

Resolution:

- Added deterministic dismissal for common consent overlays.
- Filtered known consent-management UI from runtime text extraction.
- Added fixture coverage to prevent regressions.

## Residual findings

### SEC-004 Low: scanning arbitrary sites still executes untrusted JavaScript by design

Impact: This tool intentionally loads third-party pages in Playwright, so hostile sites can still consume browser resources or attempt browser-level abuse.

Status: Residual operational risk.

Evidence:

- `src/font_audit_crawler/browser/page_loader.py:178`
- `docs/security.md:41`
- `SECURITY.md:20`

Recommendation:

- Run scans in isolated CI runners, containers, or VMs when targeting untrusted sites.
- Apply outbound network restrictions where practical.
- Treat generated reports as untrusted captured content.

## Assurance notes

- No AI or LLM runtime logic was found in the application core.
- Classification remains deterministic and YAML-driven.
- The current release does not handle credentials or authenticated sessions, which reduces the secret-handling attack surface for now.
