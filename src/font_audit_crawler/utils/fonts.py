from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import quote_plus

from font_audit_crawler.models.config_models import FailOnSeverity
from font_audit_crawler.models.findings import Severity

if TYPE_CHECKING:
    from font_audit_crawler.models.rules import ApprovedFontFamily, RulesBundle

GENERIC_FONT_FAMILIES = {
    "serif",
    "sansserif",
    "monospace",
    "cursive",
    "fantasy",
    "systemui",
    "ui-serif",
    "ui-sans-serif",
    "ui-monospace",
    "ui-rounded",
    "emoji",
    "math",
    "fangsong",
}


def normalize_font_name(value: str) -> str:
    lowered = value.strip().strip('"').strip("'").lower()
    lowered = re.sub(r"[\s\-_]+", "", lowered)
    return lowered


def split_font_stack(font_stack: str) -> list[str]:
    parts = [part.strip().strip('"').strip("'") for part in font_stack.split(",")]
    return [part for part in parts if part]


def primary_font(font_stack: str) -> str | None:
    fonts = split_font_stack(font_stack)
    return fonts[0] if fonts else None


def is_generic_font_family(font_name: str) -> bool:
    return normalize_font_name(font_name) in GENERIC_FONT_FAMILIES


def css_stack_for_family(family_name: str) -> str:
    return f"'{family_name}', sans-serif"


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def expected_replacement(
    *,
    primary_normalized: str,
    rules: RulesBundle,
) -> str:
    if primary_normalized in rules.mappings.explicit_mappings:
        return rules.mappings.explicit_mappings[primary_normalized]
    if any(indicator in primary_normalized for indicator in rules.mappings.condensed_indicators):
        return rules.mappings.condensed_replacement
    return rules.mappings.default_replacement


def approved_fonts_google_snippet(families: list[ApprovedFontFamily]) -> str | None:
    if not families:
        return None
    query_parts: list[str] = []
    for family in families:
        if not family.google_hosted:
            continue
        family_name = family.google_family or quote_plus(family.name)
        if family.google_weights:
            weight_list = ";".join(str(weight) for weight in family.google_weights)
            query_parts.append(f"family={family_name}:wght@{weight_list}")
        else:
            query_parts.append(f"family={family_name}")
    if not query_parts:
        return None
    query = "&".join(query_parts)
    return "\n".join(
        [
            '<link rel="preconnect" href="https://fonts.googleapis.com">',
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
            (
                f'<link href="https://fonts.googleapis.com/css2?{query}&display=swap" '
                'rel="stylesheet">'
            ),
        ]
    )


def choose_exit_code(findings_severities: list[Severity], fail_on: FailOnSeverity) -> int:
    if fail_on is FailOnSeverity.NEVER:
        return 0
    if fail_on is FailOnSeverity.MEDIUM and findings_severities:
        return 1
    if fail_on is FailOnSeverity.HIGH and Severity.HIGH in findings_severities:
        return 1
    return 0
