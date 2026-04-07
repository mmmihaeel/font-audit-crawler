# font-audit-crawler

`font-audit-crawler` is a deterministic, AI-free runtime font compliance auditor for remediation QA. It crawls same-origin pages, inspects visible typography with Playwright, detects runtime violations derived from `AGENTS.md`, and writes JSON, Markdown, and HTML reports with actionable evidence.

## What it audits

- Non-approved runtime font families
- Suspicious fallback stacks such as `Arial`, `Helvetica`, `Segoe UI`, `Open Sans`, and `Noto Sans`
- Same-origin font asset requests such as `.woff`, `.woff2`, `.ttf`, and `.otf`
- Runtime `@font-face` or embedded font loading visible through the CSSOM
- Visible inline `font-family` declarations
- Vendor/widget exception buckets
- Locale-specific fallback chains that require manual review

## Why runtime-first

Source-only remediation can look correct while runtime still exposes legacy typography through inline styles, inherited stacks, same-origin font assets, widget code, or locale fallbacks. This tool treats runtime evidence as the source of truth and turns it into QA-ready artifacts.

## Product principles

- Deterministic and rules-based
- No AI or LLM logic in runtime behavior
- YAML-driven rules for approved families, mappings, fallbacks, vendor exceptions, and locale review
- Same-origin crawl discipline with sitemap support, include/exclude rules, max depth, and max pages
- Production-minded CLI ergonomics, reports, tests, and docs

## Quick start

```bash
uv sync --extra dev
uv run playwright install chromium
uv run font-audit scan --url https://example.com
```

## CLI

```bash
uv run font-audit scan --url https://example.com --max-pages 25 --max-depth 2
uv run font-audit scan --url https://example.com --rules ./examples/rules.overrides.yaml
uv run font-audit validate-config --config ./examples/config.basic.yaml
uv run font-audit list-rules
uv run font-audit doctor
```

## Example config

```yaml
scan:
  max_pages: 50
  max_depth: 3
  viewport: both
  screenshot: finding
  fail_on: high
  sitemap: auto
  max_elements_per_page: 300
  output_formats: [json, markdown, html]
```

## Output artifacts

Each scan writes a timestamped directory under `reports/` by default:

- `report.json`
- `report.md`
- `report.html`
- `artifacts/crawl-urls.txt`
- `screenshots/`

The reports include:

- severity and finding-type summaries
- page-level scan coverage
- recommended approved-family replacements
- unresolved non-CSS issues
- vendor and locale manual-review buckets
- required `<head>` font loading guidance
- Google Fonts snippets for approved Google-hosted families

Sample fixture-generated artifacts live in `examples/reports/full-site/`.

## Repository layout

```text
src/font_audit_crawler/
  audit/        # deterministic rules engine
  browser/      # Playwright runtime collection
  crawl/        # same-origin discovery and sitemap handling
  models/       # typed config, runtime, finding, and report models
  reporting/    # JSON, Markdown, HTML writers
  rules/        # YAML rules bundle
tests/
  fixtures/     # local runtime fixture sites
  integration/  # fixture-backed scan tests
  e2e/          # CLI coverage
docs/           # MkDocs documentation
examples/       # example configs, overrides, sample outputs
```

## Development

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
uv run mkdocs build --strict
```

## Current limitations

- The first release audits runtime behavior only. It does not rewrite CSS or generate remediation patches.
- Template fragments, CMS styles, or third-party assets are only reported when they are visible at runtime.
- Authenticated crawling and JavaScript route exploration are intentionally out of scope for v1.

## Documentation

- [Architecture](docs/architecture.md)
- [CLI](docs/cli.md)
- [Rules Engine](docs/rules-engine.md)
- [Reports](docs/reports.md)
- [Testing](docs/testing.md)

## License

Apache-2.0
