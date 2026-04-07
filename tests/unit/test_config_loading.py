from __future__ import annotations

from pathlib import Path

import pytest

from font_audit_crawler.config import load_app_config, load_rules_bundle
from font_audit_crawler.models.config_models import ScreenshotMode


def test_load_rules_bundle_has_expected_sections() -> None:
    rules = load_rules_bundle()
    assert rules.is_approved("Roboto")
    assert rules.mappings.explicit_mappings["helvetica"] == "Roboto"


def test_load_app_config_reads_yaml_and_resolves_rules_path(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "rules_path: ./rules\nscan:\n  max_pages: 10\n  screenshot: page\n",
        encoding="utf-8",
    )
    config = load_app_config(config_file)
    assert config.scan.max_pages == 10
    assert config.scan.screenshot is ScreenshotMode.PAGE
    assert config.rules_path == rules_dir.resolve()


def test_load_app_config_rejects_missing_rules_path(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("rules_path: ./missing-rules\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        load_app_config(config_file)
