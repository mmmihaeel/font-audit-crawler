from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from font_audit_crawler.cli import app

runner = CliRunner()


def test_list_rules_command() -> None:
    result = runner.invoke(app, ["list-rules"])
    assert result.exit_code == 0
    assert "Bundled Rules" in result.stdout
    assert "Roboto" in result.stdout


def test_validate_config_command(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("scan:\n  max_pages: 5\n", encoding="utf-8")
    result = runner.invoke(app, ["validate-config", "--config", str(config_file)])
    assert result.exit_code == 0
    assert "Config is valid" in result.stdout
