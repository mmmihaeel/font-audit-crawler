from __future__ import annotations

from copy import deepcopy
from importlib.resources import files
from pathlib import Path
from typing import Any, cast

import yaml

from font_audit_crawler.models.config_models import AppConfig
from font_audit_crawler.models.rules import RulesBundle


def load_app_config(path: Path | None) -> AppConfig:
    if path is None:
        return AppConfig()

    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    config = AppConfig.model_validate(raw)
    if config.rules_path is not None and not config.rules_path.is_absolute():
        config.rules_path = (path.parent / config.rules_path).resolve()
    if config.rules_path is not None and not config.rules_path.exists():
        raise FileNotFoundError(f"Rules override path does not exist: {config.rules_path}")
    return config


def _load_packaged_yaml(filename: str) -> dict[str, Any]:
    rules_dir = files("font_audit_crawler").joinpath("rules")
    with rules_dir.joinpath(filename).open("r", encoding="utf-8") as handle:
        return cast(dict[str, Any], yaml.safe_load(handle) or {})


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(cast(dict[str, Any], merged[key]), value)
        else:
            merged[key] = value
    return merged


def _load_rule_overrides(path: Path) -> dict[str, Any]:
    if path.is_dir():
        merged: dict[str, Any] = {}
        for file_name in [
            "approved_fonts.yaml",
            "mappings.yaml",
            "fallback_blacklist.yaml",
            "vendor_exceptions.yaml",
            "locale_fallbacks.yaml",
        ]:
            override_file = path / file_name
            if override_file.exists():
                with override_file.open("r", encoding="utf-8") as handle:
                    payload = yaml.safe_load(handle) or {}
                section_name = {
                    "approved_fonts.yaml": "approved",
                    "mappings.yaml": "mappings",
                    "fallback_blacklist.yaml": "fallbacks",
                    "vendor_exceptions.yaml": "vendors",
                    "locale_fallbacks.yaml": "locale",
                }[file_name]
                merged[section_name] = payload
        return merged

    with path.open("r", encoding="utf-8") as handle:
        return cast(dict[str, Any], yaml.safe_load(handle) or {})


def load_rules_bundle(override_path: Path | None = None) -> RulesBundle:
    bundle: dict[str, Any] = {
        "approved": _load_packaged_yaml("approved_fonts.yaml"),
        "mappings": _load_packaged_yaml("mappings.yaml"),
        "fallbacks": _load_packaged_yaml("fallback_blacklist.yaml"),
        "vendors": _load_packaged_yaml("vendor_exceptions.yaml"),
        "locale": _load_packaged_yaml("locale_fallbacks.yaml"),
    }
    if override_path is not None:
        if not override_path.exists():
            raise FileNotFoundError(f"Rules override path does not exist: {override_path}")
        bundle = _deep_merge(bundle, _load_rule_overrides(override_path))
    return RulesBundle.model_validate(bundle)
