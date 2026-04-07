from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path

from typer.testing import CliRunner

from font_audit_crawler.cli import app

runner = CliRunner()


def test_cli_scan_writes_expected_artifacts(
    fixture_server: Callable[[str], AbstractContextManager[str]],
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "reports"
    with fixture_server("full-site") as base_url:
        result = runner.invoke(
            app,
            [
                "scan",
                "--url",
                base_url,
                "--output",
                str(output_root),
                "--max-pages",
                "20",
                "--max-depth",
                "2",
                "--screenshot",
                "none",
            ],
        )

    assert result.exit_code == 1
    report_dirs = list(output_root.iterdir())
    assert len(report_dirs) == 1
    report_dir = report_dirs[0]
    assert (report_dir / "report.json").exists()
    assert (report_dir / "report.md").exists()
    assert (report_dir / "report.html").exists()
    assert (report_dir / "artifacts" / "crawl-urls.txt").exists()
