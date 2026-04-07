# Contributing

## Local setup

```bash
uv sync --extra dev
uv run playwright install chromium
uv run pre-commit install
```

## Verification

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
uv run mkdocs build --strict
```

## Fixture report refresh

```bash
uv run python scripts/generate_fixture_report.py
```

## Notes

- Keep runtime behavior deterministic and AI-free.
- Keep rules changes in YAML where practical.
- Prefer fixture-backed tests over synthetic-only coverage for runtime behavior.
