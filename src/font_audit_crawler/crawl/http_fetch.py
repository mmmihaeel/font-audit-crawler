from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class TextFetchResult:
    text: str
    content_type: str


def fetch_bounded_text(
    client: httpx.Client,
    url: str,
    *,
    max_bytes: int,
) -> TextFetchResult | None:
    with client.stream("GET", url) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > max_bytes:
                    return None
            except ValueError:
                pass

        chunks: list[bytes] = []
        total_bytes = 0
        for chunk in response.iter_bytes():
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                return None
            chunks.append(chunk)

    encoding = response.encoding or "utf-8"
    body = b"".join(chunks).decode(encoding, errors="replace")
    return TextFetchResult(text=body, content_type=content_type)
