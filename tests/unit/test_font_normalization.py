from __future__ import annotations

from font_audit_crawler.config import load_rules_bundle
from font_audit_crawler.utils.fonts import (
    css_stack_for_family,
    expected_replacement,
    normalize_font_name,
    primary_font,
    split_font_stack,
)


def test_normalize_font_name_removes_quotes_spaces_and_hyphens() -> None:
    assert normalize_font_name('"Helvetica Neue"') == "helveticaneue"
    assert normalize_font_name("Roboto Condensed") == "robotocondensed"


def test_split_font_stack() -> None:
    assert split_font_stack('"Gotham Narrow", Arial, sans-serif') == [
        "Gotham Narrow",
        "Arial",
        "sans-serif",
    ]


def test_primary_font() -> None:
    assert primary_font('"Gotham Narrow", Arial, sans-serif') == "Gotham Narrow"


def test_expected_replacement_uses_condensed_rules() -> None:
    rules = load_rules_bundle()
    assert (
        expected_replacement(primary_normalized="gothamnarrow", rules=rules) == "Roboto Condensed"
    )


def test_css_stack_for_family() -> None:
    assert css_stack_for_family("Roboto") == "'Roboto', sans-serif"
