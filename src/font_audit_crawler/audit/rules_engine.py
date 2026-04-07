from __future__ import annotations

from hashlib import sha1
from typing import Any

from font_audit_crawler.audit.locale_review import locale_fallbacks_in_stack
from font_audit_crawler.audit.vendor_detection import is_vendor_exception
from font_audit_crawler.models.findings import Finding, FindingType, FontRecommendation, Severity
from font_audit_crawler.models.rules import RulesBundle
from font_audit_crawler.models.runtime import (
    FontRequest,
    PageRuntimeSnapshot,
    RuntimeFontFaceRule,
    RuntimeTextElement,
)
from font_audit_crawler.utils.fonts import (
    css_stack_for_family,
    expected_replacement,
    normalize_font_name,
    primary_font,
    split_font_stack,
)
from font_audit_crawler.utils.strings import truncate


def _finding_id(
    finding_type: FindingType,
    url: str,
    viewport: str,
    selector: str | None,
    discriminator: str,
) -> str:
    payload = "|".join([finding_type.value, url, viewport, selector or "", discriminator])
    return sha1(payload.encode("utf-8")).hexdigest()[:12]


def _font_recommendation(
    family_name: str,
    font_weight: str,
    font_style: str,
) -> FontRecommendation:
    return FontRecommendation(
        family=family_name,
        css_stack=css_stack_for_family(family_name),
        font_weight=font_weight,
        font_style=font_style,
    )


def _dedupe_findings(findings: list[Finding]) -> list[Finding]:
    deduped: dict[str, Finding] = {}
    for finding in findings:
        deduped[finding.id] = finding
    return sorted(
        deduped.values(),
        key=lambda item: (item.url, item.viewport, item.type.value, item.selector or "", item.id),
    )


def _merge_list(values: list[str], new_values: list[str], *, limit: int = 10) -> list[str]:
    merged = list(values)
    for value in new_values:
        if value and value not in merged:
            merged.append(value)
        if len(merged) >= limit:
            break
    return merged


def _aggregate_findings(findings: list[Finding]) -> list[Finding]:
    aggregate_types = {
        FindingType.RUNTIME_NON_APPROVED_FONT,
        FindingType.SUSPICIOUS_FALLBACK_STACK,
        FindingType.LOCALE_FALLBACK_REVIEW,
        FindingType.VENDOR_EXCEPTION,
    }
    grouped: dict[tuple[Any, ...], Finding] = {}
    passthrough: list[Finding] = []

    for finding in findings:
        if finding.type not in aggregate_types:
            passthrough.append(finding)
            continue

        recommended_family = finding.recommended.family if finding.recommended else None
        key = (
            finding.type,
            finding.url,
            finding.viewport,
            finding.primary_font,
            finding.font_stack,
            recommended_family,
        )
        if key not in grouped:
            base_evidence = dict(finding.evidence)
            base_evidence["occurrences"] = 1
            base_evidence["sample_selectors"] = [finding.selector] if finding.selector else []
            base_evidence["sample_texts"] = [finding.text_sample] if finding.text_sample else []
            grouped[key] = finding.model_copy(
                update={
                    "selector": None,
                    "text_sample": None,
                    "evidence": base_evidence,
                }
            )
            continue

        existing = grouped[key]
        evidence = dict(existing.evidence)
        evidence["occurrences"] = int(evidence.get("occurrences", 1)) + 1
        evidence["sample_selectors"] = _merge_list(
            list(evidence.get("sample_selectors", [])),
            [finding.selector] if finding.selector else [],
        )
        evidence["sample_texts"] = _merge_list(
            list(evidence.get("sample_texts", [])),
            [finding.text_sample] if finding.text_sample else [],
            limit=5,
        )
        if finding.note and existing.note and "Observed on" not in existing.note:
            evidence["note_detail"] = finding.note
        grouped[key] = existing.model_copy(update={"evidence": evidence})

    combined = passthrough + list(grouped.values())
    return _dedupe_findings(combined)


def classify_element(
    element: RuntimeTextElement,
    page: PageRuntimeSnapshot,
    rules: RulesBundle,
) -> list[Finding]:
    findings: list[Finding] = []
    stack = split_font_stack(element.font_family)
    first = primary_font(element.font_family)
    if not first:
        return findings

    normalized_primary = normalize_font_name(first)
    if is_vendor_exception(element, stack, rules):
        findings.append(
            Finding(
                id=_finding_id(
                    FindingType.VENDOR_EXCEPTION,
                    page.url,
                    page.viewport,
                    element.selector,
                    element.font_family,
                ),
                type=FindingType.VENDOR_EXCEPTION,
                severity=Severity.MANUAL_REVIEW,
                url=page.url,
                viewport=page.viewport,
                selector=element.selector,
                text_sample=truncate(element.text),
                font_stack=element.font_family,
                primary_font=first,
                normalized_primary_font=normalized_primary,
                note="Vendor or widget-owned runtime typography. Leave as a manual-review bucket.",
            )
        )
        return findings

    locale_matches = locale_fallbacks_in_stack(stack, rules)
    primary_requires_locale_review = normalized_primary in rules.normalized_locale_fallbacks
    if locale_matches:
        note = (
            "Locale-specific fallback chain present at runtime. "
            "Keep only if script coverage requires it; otherwise review manually."
        )
        if primary_requires_locale_review:
            note = (
                "Locale-specific primary runtime font detected. "
                "Review script coverage manually before replacing it with a Latin-default family."
            )
        findings.append(
            Finding(
                id=_finding_id(
                    FindingType.LOCALE_FALLBACK_REVIEW,
                    page.url,
                    page.viewport,
                    element.selector,
                    "|".join(locale_matches),
                ),
                type=FindingType.LOCALE_FALLBACK_REVIEW,
                severity=Severity.MANUAL_REVIEW,
                url=page.url,
                viewport=page.viewport,
                selector=element.selector,
                text_sample=truncate(element.text),
                font_stack=element.font_family,
                primary_font=first,
                normalized_primary_font=normalized_primary,
                evidence={"locale_fallbacks": locale_matches},
                note=note,
            )
        )

    if not rules.is_approved(first) and not primary_requires_locale_review:
        recommended_family = expected_replacement(
            primary_normalized=normalized_primary,
            rules=rules,
        )
        findings.append(
            Finding(
                id=_finding_id(
                    FindingType.RUNTIME_NON_APPROVED_FONT,
                    page.url,
                    page.viewport,
                    element.selector,
                    normalized_primary,
                ),
                type=FindingType.RUNTIME_NON_APPROVED_FONT,
                severity=Severity.HIGH,
                url=page.url,
                viewport=page.viewport,
                selector=element.selector,
                text_sample=truncate(element.text),
                font_stack=element.font_family,
                primary_font=first,
                normalized_primary_font=normalized_primary,
                recommended=_font_recommendation(
                    recommended_family,
                    element.font_weight,
                    element.font_style,
                ),
                evidence={
                    "font_weight": element.font_weight,
                    "font_style": element.font_style,
                    "element_audit_id": element.audit_id,
                },
                note="Primary runtime font family is not approved.",
            )
        )

    disallowed_present = [
        item for item in stack if normalize_font_name(item) in rules.normalized_fallbacks
    ]
    suspicious_aliases = [
        item for item in stack if normalize_font_name(item) in rules.normalized_aliases
    ]
    if disallowed_present or suspicious_aliases:
        findings.append(
            Finding(
                id=_finding_id(
                    FindingType.SUSPICIOUS_FALLBACK_STACK,
                    page.url,
                    page.viewport,
                    element.selector,
                    "|".join(disallowed_present + suspicious_aliases),
                ),
                type=FindingType.SUSPICIOUS_FALLBACK_STACK,
                severity=Severity.MEDIUM,
                url=page.url,
                viewport=page.viewport,
                selector=element.selector,
                text_sample=truncate(element.text),
                font_stack=element.font_family,
                primary_font=first,
                normalized_primary_font=normalized_primary,
                evidence={
                    "disallowed_fallbacks": disallowed_present,
                    "suspicious_aliases": suspicious_aliases,
                },
                note=(
                    "Fallback stack still contains legacy fallback fonts or unexplained aliases. "
                    "Collapse to the approved family plus the generic fallback only."
                ),
            )
        )

    inline_style = element.inline_style or ""
    if "font-family" in inline_style.lower():
        findings.append(
            Finding(
                id=_finding_id(
                    FindingType.INLINE_FONT_DECLARATION,
                    page.url,
                    page.viewport,
                    element.selector,
                    inline_style,
                ),
                type=FindingType.INLINE_FONT_DECLARATION,
                severity=Severity.HIGH,
                url=page.url,
                viewport=page.viewport,
                selector=element.selector,
                text_sample=truncate(element.text),
                font_stack=element.font_family,
                primary_font=first,
                normalized_primary_font=normalized_primary,
                evidence={"inline_style": inline_style},
                note=(
                    "Visible inline font-family declaration detected. This is an unresolved inline "
                    "or template-level typography issue."
                ),
            )
        )

    return findings


def classify_font_face(
    page: PageRuntimeSnapshot,
    font_face: RuntimeFontFaceRule,
    rules: RulesBundle,
) -> list[Finding]:
    if not font_face.has_data_uri and not font_face.has_local_url:
        return []

    recommended_family = (
        font_face.font_family
        if rules.is_approved(font_face.font_family)
        else expected_replacement(
            primary_normalized=normalize_font_name(font_face.font_family),
            rules=rules,
        )
    )
    finding = Finding(
        id=_finding_id(
            FindingType.LOCAL_CSS_FONT_FACE,
            page.url,
            page.viewport,
            font_face.stylesheet_url,
            font_face.src,
        ),
        type=FindingType.LOCAL_CSS_FONT_FACE,
        severity=Severity.HIGH,
        url=page.url,
        viewport=page.viewport,
        font_stack=font_face.font_family,
        primary_font=font_face.font_family,
        normalized_primary_font=normalize_font_name(font_face.font_family),
        recommended=_font_recommendation(recommended_family, "400", "normal"),
        evidence={
            "src": font_face.src,
            "stylesheet_url": font_face.stylesheet_url,
            "same_origin_urls": font_face.same_origin_urls,
            "has_data_uri": font_face.has_data_uri,
        },
        note=(
            "Runtime CSS exposes @font-face or embedded font loading. "
            "Local theme CSS must not load fonts, even when the family itself is approved."
        ),
    )
    return [finding]


def classify_font_request(page: PageRuntimeSnapshot, request: FontRequest) -> list[Finding]:
    if not request.same_origin:
        return []
    finding = Finding(
        id=_finding_id(
            FindingType.LOCAL_FONT_ASSET_LOADED,
            page.url,
            page.viewport,
            None,
            request.url,
        ),
        type=FindingType.LOCAL_FONT_ASSET_LOADED,
        severity=Severity.HIGH,
        url=page.url,
        viewport=page.viewport,
        evidence={"request_url": request.url, "resource_type": request.resource_type},
        note=(
            "A same-origin font asset was requested at runtime. Approved fonts loaded from local "
            "assets are still a compliance failure."
        ),
    )
    return [finding]


def classify_page(page: PageRuntimeSnapshot, rules: RulesBundle) -> list[Finding]:
    findings: list[Finding] = []
    if page.page_error:
        findings.append(
            Finding(
                id=_finding_id(
                    FindingType.PAGE_LOAD_ERROR,
                    page.url,
                    page.viewport,
                    None,
                    page.page_error,
                ),
                type=FindingType.PAGE_LOAD_ERROR,
                severity=Severity.MEDIUM,
                url=page.url,
                viewport=page.viewport,
                evidence={"page_error": page.page_error},
                note="Page failed to load cleanly, so runtime typography coverage is incomplete.",
            )
        )
        return findings

    for element in page.elements:
        findings.extend(classify_element(element, page, rules))

    for font_face in page.font_face_rules:
        findings.extend(classify_font_face(page, font_face, rules))

    seen_request_urls: set[str] = set()
    for request in page.font_requests:
        if request.url in seen_request_urls:
            continue
        seen_request_urls.add(request.url)
        findings.extend(classify_font_request(page, request))

    return _aggregate_findings(findings)
