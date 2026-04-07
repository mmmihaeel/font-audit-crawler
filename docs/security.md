# Security

## Security model

`font-audit-crawler` is a local operator tool. It is not a hosted service and it does not expose a remote API surface. The primary security concerns are:

- scanning untrusted external pages
- processing untrusted runtime text and CSS
- avoiding report rendering issues
- keeping runtime behavior deterministic and auditable

## Secure-by-default choices

| Area | Current posture |
| --- | --- |
| Crawl scope | Same-origin only |
| URL normalization | Removes fragments and blocks unsafe schemes |
| Response size | Sitemap and crawl HTML discovery use bounded fetch limits |
| Browser runtime | Runs in Playwright Chromium with a fresh context per page |
| Consent UI handling | Known consent and cookie UI are dismissed or excluded from findings |
| HTML report rendering | Jinja autoescaping plus restrictive CSP and `referrer` policy |
| AI usage | None in runtime behavior |

## Deterministic and non-AI behavior

The runtime engine does not use:

- prompts
- embeddings
- model inference
- heuristic AI classification
- generative remediation

All classification decisions come from:

- YAML rules
- computed browser styles
- observed network requests
- deterministic aggregation logic

## Operational best practices

- Run scans in a dedicated runner when targeting untrusted sites.
- Treat report artifacts as untrusted because they may contain captured page text.
- Keep the default same-origin crawl boundaries unless you have a controlled use case.
- Review vendor/manual-review buckets before assuming a site is clean.
- Keep Playwright and Python dependencies current through normal patch maintenance.

## Residual risks

- Scanning arbitrary sites still executes third-party JavaScript in a browser context by design.
- A site can still be slow, unstable, or deliberately hostile, so isolation matters operationally.
- The current release does not include authenticated crawling, secret handling, or source rewriting.
