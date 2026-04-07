from __future__ import annotations

import shutil
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

FIXTURE_SITES = Path(__file__).parent / "fixtures" / "sites"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return None


@contextmanager
def serve_site_directory(directory: Path) -> Iterator[str]:
    handler = partial(QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    sitemap = directory / "sitemap.xml"
    if sitemap.exists():
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


@pytest.fixture()
def fixture_server(tmp_path: Path) -> Iterator[Callable[[str], AbstractContextManager[str]]]:
    def _start(site_name: str) -> AbstractContextManager[str]:
        source = FIXTURE_SITES / site_name
        target = tmp_path / site_name
        shutil.copytree(source, target)
        return serve_site_directory(target)

    yield _start
