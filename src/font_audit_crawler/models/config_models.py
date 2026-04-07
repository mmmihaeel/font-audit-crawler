from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ViewportMode(StrEnum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    BOTH = "both"


class ScreenshotMode(StrEnum):
    NONE = "none"
    PAGE = "page"
    FINDING = "finding"


class FailOnSeverity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    NEVER = "never"


class SitemapMode(StrEnum):
    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"


class ReportFormat(StrEnum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class ScanConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_pages: int = Field(default=25, ge=1, le=10_000)
    max_depth: int = Field(default=2, ge=0, le=20)
    max_page_bytes: int = Field(default=2_000_000, ge=32_768, le=50_000_000)
    max_sitemap_bytes: int = Field(default=1_000_000, ge=16_384, le=10_000_000)
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)
    viewport: ViewportMode = ViewportMode.DESKTOP
    screenshot: ScreenshotMode = ScreenshotMode.FINDING
    fail_on: FailOnSeverity = FailOnSeverity.HIGH
    sitemap: SitemapMode = SitemapMode.AUTO
    timeout_ms: int = Field(default=30_000, ge=1_000, le=120_000)
    wait_after_load_ms: int = Field(default=750, ge=0, le=30_000)
    max_elements_per_page: int = Field(default=250, ge=1, le=2_000)
    keep_query_strings: bool = False
    output_formats: list[ReportFormat] = Field(
        default_factory=lambda: [ReportFormat.JSON, ReportFormat.MARKDOWN, ReportFormat.HTML]
    )


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scan: ScanConfig = Field(default_factory=ScanConfig)
    rules_path: Path | None = None
