#!/usr/bin/env bash
set -euo pipefail

uv sync --extra dev
uv run playwright install chromium
uv run font-audit scan --url https://example.com --max-pages 5 --screenshot none
