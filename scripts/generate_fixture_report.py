from __future__ import annotations

import asyncio
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from font_audit_crawler.models.config_models import AppConfig, ScreenshotMode
from font_audit_crawler.reporting.html_report import write_html_report
from font_audit_crawler.reporting.json_report import write_json_report
from font_audit_crawler.reporting.markdown_report import write_markdown_report
from font_audit_crawler.scanner import run_scan

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SITE = ROOT / "tests" / "fixtures" / "sites" / "full-site"
OUTPUT_DIR = ROOT / "examples" / "reports" / "full-site"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return None


@contextmanager
def serve_site(directory: Path) -> Iterator[str]:
    handler = partial(QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    sitemap = directory / "sitemap.xml"
    sitemap.write_text(
        sitemap.read_text(encoding="utf-8").replace("{{BASE_URL}}", base_url),
        encoding="utf-8",
    )
    try:
        yield base_url
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def main() -> None:
    fixture_copy = ROOT / ".tmp" / "fixture-site"
    if fixture_copy.exists():
        shutil.rmtree(fixture_copy)
    shutil.copytree(FIXTURE_SITE, fixture_copy)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = AppConfig()
    config.scan.max_pages = 20
    config.scan.max_depth = 2
    config.scan.screenshot = ScreenshotMode.NONE

    with serve_site(fixture_copy) as base_url:
        report = asyncio.run(run_scan(start_url=base_url, config=config, output_dir=OUTPUT_DIR))

    write_json_report(OUTPUT_DIR / "report.json", report)
    write_markdown_report(OUTPUT_DIR / "report.md", report)
    write_html_report(OUTPUT_DIR / "report.html", report)
    (OUTPUT_DIR / "crawl-urls.txt").write_text("\n".join(report.scanned_urls), encoding="utf-8")

    shutil.rmtree(fixture_copy)


if __name__ == "__main__":
    main()
