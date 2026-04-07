from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CrawlResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_url: str
    urls: list[str]
    sitemap_urls: list[str] = Field(default_factory=list)
