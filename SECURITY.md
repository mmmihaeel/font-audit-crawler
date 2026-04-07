# Security Policy

## Supported versions

Only the latest tagged release is considered supported for security hardening and documentation updates.

## Reporting a vulnerability

If you find a vulnerability in `font-audit-crawler`, open a private security advisory or contact the maintainer directly before publishing details publicly.

When reporting, include:

- affected version or commit
- reproduction steps
- impact assessment
- suggested mitigation if you have one

## Security posture

This project is designed as an operator-run CLI, not a multi-tenant web service. Its runtime posture is:

- deterministic and AI-free
- same-origin crawl only
- bounded network fetch sizes for crawl and sitemap discovery
- no credential handling in the current release
- autoescaped HTML reporting with a restrictive CSP

## Operational guidance

- Run scans for untrusted public targets in an isolated container, VM, or CI runner.
- Restrict outbound network access where practical.
- Treat generated reports as untrusted content because they may contain text captured from third-party pages.
- Avoid committing internal target reports if they may contain sensitive runtime text.
