from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from font_audit_crawler.models.reports import SiteReport


def write_html_report(path: Path, report: SiteReport) -> None:
    template_dir = files("font_audit_crawler").joinpath("reporting/templates")
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml", "j2")),
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )
    template = env.get_template("report.html.j2")
    path.write_text(template.render(report=report), encoding="utf-8")
