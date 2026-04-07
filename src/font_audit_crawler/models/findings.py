from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    MANUAL_REVIEW = "manual_review"


class FindingType(StrEnum):
    RUNTIME_NON_APPROVED_FONT = "runtime_non_approved_font"
    SUSPICIOUS_FALLBACK_STACK = "suspicious_fallback_stack"
    LOCAL_FONT_ASSET_LOADED = "local_font_asset_loaded"
    LOCAL_CSS_FONT_FACE = "local_css_font_face"
    INLINE_FONT_DECLARATION = "inline_font_declaration"
    VENDOR_EXCEPTION = "vendor_exception"
    LOCALE_FALLBACK_REVIEW = "locale_fallback_review"
    PAGE_LOAD_ERROR = "page_load_error"


class FontRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: str
    css_stack: str
    font_weight: str
    font_style: str


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = ""
    type: FindingType
    severity: Severity
    url: str
    viewport: str
    selector: str | None = None
    text_sample: str | None = None
    font_stack: str | None = None
    primary_font: str | None = None
    normalized_primary_font: str | None = None
    recommended: FontRecommendation | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    note: str | None = None
    screenshot_path: str | None = None
