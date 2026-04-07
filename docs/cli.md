# CLI

## Primary command

```bash
font-audit scan --url https://example.com
```

## Scan options

| Option | Purpose |
| --- | --- |
| `--url` | Root URL to scan |
| `--output` | Output directory root |
| `--config` | YAML config file |
| `--rules` | Rules override file or directory |
| `--max-pages` | Hard cap on visited pages |
| `--max-depth` | Breadth-first crawl depth limit |
| `--timeout-ms` | Per-page browser timeout |
| `--max-page-bytes` | Maximum bytes to read while discovering HTML pages |
| `--max-sitemap-bytes` | Maximum bytes to read while discovering sitemap XML |
| `--include` | Include glob or `re:` pattern |
| `--exclude` | Exclude glob or `re:` pattern |
| `--viewport` | `desktop`, `mobile`, or `both` |
| `--screenshot` | `none`, `page`, or `finding` |
| `--sitemap` | `auto`, `always`, or `never` |
| `--fail-on` | `high`, `medium`, or `never` |
| `--verbose` | Enable verbose logging |

## Examples

```bash
font-audit scan --url https://example.com --max-pages 50 --max-depth 3
font-audit scan --url https://example.com --include "/products/*" --exclude "re:/checkout"
font-audit scan --url https://example.com --viewport both --screenshot page
font-audit scan --url https://example.com --timeout-ms 45000 --max-page-bytes 2000000
font-audit scan --url https://example.com --config ./examples/config.strict.yaml
font-audit scan --url https://example.com --rules ./examples/rules.overrides.yaml
```

## Helper commands

```bash
font-audit validate-config --config ./examples/config.basic.yaml
font-audit list-rules
font-audit doctor
```

## Config file

Example:

```yaml
scan:
  max_pages: 25
  max_depth: 2
  max_page_bytes: 2000000
  max_sitemap_bytes: 1000000
  viewport: desktop
  screenshot: finding
  fail_on: high
  sitemap: auto
  keep_query_strings: false
  max_elements_per_page: 250
  output_formats: [json, markdown, html]
rules_path: ./rules.overrides.yaml
```

## Exit codes

| Exit code | Meaning |
| --- | --- |
| `0` | No findings at the configured fail threshold |
| `1` | Findings met the configured fail threshold |
| `2+` | CLI or environment failure |
