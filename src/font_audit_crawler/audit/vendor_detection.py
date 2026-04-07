from __future__ import annotations

from font_audit_crawler.models.rules import RulesBundle
from font_audit_crawler.models.runtime import RuntimeTextElement
from font_audit_crawler.utils.fonts import normalize_font_name


def is_vendor_exception(element: RuntimeTextElement, stack: list[str], rules: RulesBundle) -> bool:
    normalized_stack = {normalize_font_name(font) for font in stack}
    if normalized_stack & rules.normalized_vendor_fonts:
        return True

    selector_tokens = [element.selector, element.id_attribute or ""]
    selector_tokens.extend(element.class_names)
    normalized_selector = normalize_font_name(" ".join(selector_tokens))
    return any(keyword in normalized_selector for keyword in rules.normalized_vendor_keywords)
