# Changelog

## 0.1.1

- Added bounded sitemap and crawl HTML fetch limits for safer discovery on untrusted targets
- Added stricter HTML report rendering via Jinja `StrictUndefined` and a restrictive CSP
- Added deterministic filtering for consent-management UI from runtime evidence
- Routed locale-specific primary fonts such as `Noto Sans JP` into manual review instead of unsafe default replacement advice
- Added security documentation and repository security policy

## 0.1.0

- Rebuilt the starter into a deterministic runtime font auditing CLI named `font-audit`
- Added typed crawl, runtime, finding, report, and rules models
- Implemented same-origin crawling with sitemap discovery and include/exclude filters
- Implemented Playwright runtime extraction for visible text, CSS `@font-face`, and font asset requests
- Added a YAML-driven rules engine aligned to `AGENTS.md`
- Added JSON, Markdown, and HTML report generation with `<head>` loading guidance
- Added fixture-backed unit, integration, and end-to-end tests
- Added example configs, rules overrides, sample reports, MkDocs documentation, CI, and pre-commit hooks

## Pre-release

- Initial starter scaffold
