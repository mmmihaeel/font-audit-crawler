# Reports

Each scan writes a timestamped output directory containing report artifacts and optional screenshots.

## Files

| File | Purpose |
| --- | --- |
| `report.json` | Machine-readable source of truth |
| `report.md` | Text-first review and diff-friendly output |
| `report.html` | Human-friendly report with summary panels and linked screenshots |
| `artifacts/crawl-urls.txt` | Final discovered URL list |
| `screenshots/` | Page screenshots when enabled |

## Rendering safety

The HTML report is intended to be opened locally, but it still applies:

- Jinja autoescaping
- restrictive CSP via a meta tag
- `referrer` suppression

This reduces the chance that captured runtime text can execute or leak context when the report is opened.

## Report sections

The report model includes:

- scan summary
- crawl summary
- per-page coverage
- flat findings list
- recommended family replacements
- unresolved non-CSS issues
- vendor and locale manual-review buckets, including locale-specific primary runtime families
- `<head>` font loading guidance

## Head guidance behavior

When the scan determines that approved Google-hosted families are required, it emits a ready-to-paste snippet like:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@100;300;400;500;700;800;900&family=Roboto+Condensed:wght@300;400;700&display=swap" rel="stylesheet">
```

When a required family is approved but not assumed to be Google-hosted, the report emits a note instead of fabricating a URL.

## Screenshot strategy

- `screenshot: none`: no screenshots
- `screenshot: page`: every scanned page gets a screenshot
- `screenshot: finding`: only pages with findings get screenshots

## JSON as the integration surface

`report.json` is the best output for downstream processing because it contains the full typed report:

- page summaries
- finding evidence
- recommended approved-family replacements
- head requirements
- manual-review buckets
