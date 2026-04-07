from __future__ import annotations

from pathlib import Path

import orjson

from font_audit_crawler.models.reports import SiteReport


def write_json_report(path: Path, report: SiteReport) -> None:
    path.write_bytes(
        orjson.dumps(
            report.model_dump(mode="json"),
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )
    )
