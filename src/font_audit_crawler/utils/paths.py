from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from slugify import slugify


def make_output_dir(root: Path | None, site_url: str) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    target_root = root or Path("reports")
    target = target_root / f"{slugify(site_url)}-{timestamp}"
    target.mkdir(parents=True, exist_ok=True)
    (target / "artifacts").mkdir(exist_ok=True)
    (target / "screenshots").mkdir(exist_ok=True)
    return target


def relative_to(base: Path, target: Path | None) -> str | None:
    if target is None:
        return None
    return str(target.relative_to(base))
