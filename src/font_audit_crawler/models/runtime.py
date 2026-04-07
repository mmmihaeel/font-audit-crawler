from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    width: float
    height: float


class RuntimeTextElement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    selector: str
    text: str
    font_family: str
    font_weight: str
    font_style: str
    inline_style: str | None = None
    tag_name: str
    class_names: list[str] = Field(default_factory=list)
    id_attribute: str | None = None
    bounding_box: BoundingBox | None = None


class RuntimeFontFaceRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    font_family: str
    src: str
    stylesheet_url: str | None = None
    source_kind: str
    urls: list[str] = Field(default_factory=list)
    has_data_uri: bool = False
    has_local_url: bool = False
    same_origin_urls: list[str] = Field(default_factory=list)


class FontRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    resource_type: str
    same_origin: bool


class PageRuntimeSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    viewport: str
    elements: list[RuntimeTextElement] = Field(default_factory=list)
    font_face_rules: list[RuntimeFontFaceRule] = Field(default_factory=list)
    font_requests: list[FontRequest] = Field(default_factory=list)
    page_screenshot_path: str | None = None
    page_error: str | None = None
