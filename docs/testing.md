# Testing

The repository includes unit, integration, and end-to-end coverage with local fixture sites.

## Test layers

| Layer | Scope |
| --- | --- |
| Unit | normalization, config loading, rules engine decisions, CLI helper commands |
| Integration | runtime scans against local fixture sites served over HTTP |
| E2E | CLI scan execution and artifact generation |

## Fixture coverage

The local fixture sites cover:

- approved-only typography
- bad local `@font-face`
- suspicious fallback stacks
- non-approved legacy font usage
- inline style leftovers
- vendor/widget exception buckets
- locale-specific fallback review
- full multi-page site with `sitemap.xml`

## Commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
uv run mkdocs build --strict
```

## Playwright requirement

Install Chromium before running integration or e2e coverage:

```bash
uv run playwright install chromium
```

## Why fixture-backed runtime tests matter

The main product promise is runtime auditing, not source inspection. The integration tests prove that the engine catches actual computed font stacks, same-origin font asset requests, runtime `@font-face` rules, and visible inline font declarations in a browser session.
