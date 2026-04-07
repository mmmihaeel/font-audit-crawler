from __future__ import annotations

from pathlib import Path

from font_audit_crawler.utils.paths import relative_to


def test_relative_to_uses_posix_separator() -> None:
    base = Path("reports")
    target = Path("reports") / "screenshots" / "page.png"

    assert relative_to(base, target) == "screenshots/page.png"
