from __future__ import annotations

from functools import cached_property

from pydantic import BaseModel, ConfigDict, Field

from font_audit_crawler.utils.fonts import normalize_font_name


class ApprovedFontFamily(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    google_hosted: bool = False
    google_family: str | None = None
    google_weights: list[int] = Field(default_factory=list)

    @property
    def normalized_name(self) -> str:
        return normalize_font_name(self.name)


class ApprovedFontsRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved_families: list[ApprovedFontFamily]


class MappingRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    explicit_mappings: dict[str, str]
    default_replacement: str
    condensed_replacement: str
    condensed_indicators: list[str]
    known_legacy_families: list[str] = Field(default_factory=list)


class FallbackRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disallowed_fallbacks: list[str]
    suspicious_aliases: list[str] = Field(default_factory=list)


class VendorRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vendor_font_exceptions: list[str]
    vendor_selector_keywords: list[str] = Field(default_factory=list)


class LocaleRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locale_fallbacks: list[str]


class RulesBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: ApprovedFontsRules
    mappings: MappingRules
    fallbacks: FallbackRules
    vendors: VendorRules
    locale: LocaleRules

    @cached_property
    def approved_by_normalized(self) -> dict[str, ApprovedFontFamily]:
        return {family.normalized_name: family for family in self.approved.approved_families}

    @cached_property
    def normalized_fallbacks(self) -> set[str]:
        return {normalize_font_name(item) for item in self.fallbacks.disallowed_fallbacks}

    @cached_property
    def normalized_aliases(self) -> set[str]:
        return {normalize_font_name(item) for item in self.fallbacks.suspicious_aliases}

    @cached_property
    def normalized_vendor_fonts(self) -> set[str]:
        return {normalize_font_name(item) for item in self.vendors.vendor_font_exceptions}

    @cached_property
    def normalized_vendor_keywords(self) -> set[str]:
        return {normalize_font_name(item) for item in self.vendors.vendor_selector_keywords}

    @cached_property
    def normalized_locale_fallbacks(self) -> set[str]:
        return {normalize_font_name(item) for item in self.locale.locale_fallbacks}

    def is_approved(self, family_name: str) -> bool:
        return normalize_font_name(family_name) in self.approved_by_normalized

    def approved_family(self, family_name: str) -> ApprovedFontFamily | None:
        return self.approved_by_normalized.get(normalize_font_name(family_name))
