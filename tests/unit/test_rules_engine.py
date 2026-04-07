from __future__ import annotations

from font_audit_crawler.audit.rules_engine import classify_page
from font_audit_crawler.config import load_rules_bundle
from font_audit_crawler.models.findings import FindingType, Severity
from font_audit_crawler.models.runtime import (
    PageRuntimeSnapshot,
    RuntimeFontFaceRule,
    RuntimeTextElement,
)


def test_non_approved_font_is_high_severity() -> None:
    rules = load_rules_bundle()
    page = PageRuntimeSnapshot(
        url="https://example.com/about",
        viewport="desktop",
        elements=[
            RuntimeTextElement(
                audit_id="fa-1",
                selector="h1",
                text="Hello world",
                font_family='"Gotham Narrow", Arial, sans-serif',
                font_weight="700",
                font_style="normal",
                tag_name="h1",
            )
        ],
    )
    findings = classify_page(page, rules)
    assert any(f.type == FindingType.RUNTIME_NON_APPROVED_FONT for f in findings)
    assert any(f.severity == Severity.HIGH for f in findings)
    assert any(
        f.recommended is not None and f.recommended.family == "Roboto Condensed" for f in findings
    )


def test_inline_font_declaration_is_reported() -> None:
    rules = load_rules_bundle()
    page = PageRuntimeSnapshot(
        url="https://example.com/about",
        viewport="desktop",
        elements=[
            RuntimeTextElement(
                audit_id="fa-1",
                selector="p",
                text="Hello world",
                font_family='"Roboto", sans-serif',
                font_weight="400",
                font_style="normal",
                inline_style="font-family: Gotham;",
                tag_name="p",
            )
        ],
    )
    findings = classify_page(page, rules)
    assert any(f.type == FindingType.INLINE_FONT_DECLARATION for f in findings)


def test_vendor_exception_short_circuits_normal_font_findings() -> None:
    rules = load_rules_bundle()
    page = PageRuntimeSnapshot(
        url="https://example.com/widget",
        viewport="desktop",
        elements=[
            RuntimeTextElement(
                audit_id="fa-1",
                selector=".userway-widget",
                text="Accessibility widget",
                font_family='"Metropolis", Arial, sans-serif',
                font_weight="400",
                font_style="normal",
                class_names=["userway-widget"],
                tag_name="div",
            )
        ],
    )
    findings = classify_page(page, rules)
    assert [finding.type for finding in findings] == [FindingType.VENDOR_EXCEPTION]


def test_locale_fallback_is_manual_review() -> None:
    rules = load_rules_bundle()
    page = PageRuntimeSnapshot(
        url="https://example.com/ja",
        viewport="desktop",
        elements=[
            RuntimeTextElement(
                audit_id="fa-1",
                selector="body",
                text="日本語の見出し",
                font_family='"Roboto", "YuGothic", Meiryo, sans-serif',
                font_weight="400",
                font_style="normal",
                tag_name="body",
            )
        ],
    )
    findings = classify_page(page, rules)
    assert any(f.type == FindingType.LOCALE_FALLBACK_REVIEW for f in findings)
    assert any(f.severity == Severity.MANUAL_REVIEW for f in findings)


def test_local_font_face_rule_is_high_severity() -> None:
    rules = load_rules_bundle()
    page = PageRuntimeSnapshot(
        url="https://example.com/theme",
        viewport="desktop",
        font_face_rules=[
            RuntimeFontFaceRule(
                font_family="Roboto",
                src="url('/fonts/RobotoRegular.woff2') format('woff2')",
                stylesheet_url="https://example.com/theme.css",
                source_kind="linked",
                has_local_url=True,
                same_origin_urls=["https://example.com/fonts/RobotoRegular.woff2"],
            )
        ],
    )
    findings = classify_page(page, rules)
    assert any(f.type == FindingType.LOCAL_CSS_FONT_FACE for f in findings)
    assert any(f.severity == Severity.HIGH for f in findings)


def test_duplicate_runtime_non_approved_font_findings_are_aggregated() -> None:
    rules = load_rules_bundle()
    page = PageRuntimeSnapshot(
        url="https://example.com/aggregate",
        viewport="desktop",
        elements=[
            RuntimeTextElement(
                audit_id="fa-1",
                selector="h1",
                text="Headline",
                font_family='"Noto Sans JP", sans-serif',
                font_weight="700",
                font_style="normal",
                tag_name="h1",
            ),
            RuntimeTextElement(
                audit_id="fa-2",
                selector="p",
                text="Body copy",
                font_family='"Noto Sans JP", sans-serif',
                font_weight="400",
                font_style="normal",
                tag_name="p",
            ),
        ],
    )
    findings = classify_page(page, rules)
    matching = [
        finding for finding in findings if finding.type is FindingType.RUNTIME_NON_APPROVED_FONT
    ]
    assert len(matching) == 1
    assert matching[0].evidence["occurrences"] == 2
