from __future__ import annotations

import httpx

from font_audit_crawler.crawl.http_fetch import fetch_bounded_text


def test_fetch_bounded_text_returns_text_within_limit() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<html>ok</html>",
        )
    )
    with httpx.Client(transport=transport) as client:
        response = fetch_bounded_text(client, "https://example.com", max_bytes=1024)

    assert response is not None
    assert response.text == "<html>ok</html>"
    assert "text/html" in response.content_type


def test_fetch_bounded_text_rejects_large_content_length() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={
                "content-type": "text/html; charset=utf-8",
                "content-length": "9999999",
            },
            text="<html>too big</html>",
        )
    )
    with httpx.Client(transport=transport) as client:
        response = fetch_bounded_text(client, "https://example.com", max_bytes=1024)

    assert response is None
