from __future__ import annotations

from font_audit_crawler.models.rules import RulesBundle
from font_audit_crawler.utils.fonts import normalize_font_name


def locale_fallbacks_in_stack(stack: list[str], rules: RulesBundle) -> list[str]:
    matches: list[str] = []
    for font in stack:
        if normalize_font_name(font) in rules.normalized_locale_fallbacks:
            matches.append(font)
    return matches
