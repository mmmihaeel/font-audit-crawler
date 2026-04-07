from __future__ import annotations

from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

DISALLOWED_SCHEMES = {"mailto", "tel", "javascript", "data", "ftp"}


def normalize_url(
    url: str,
    base_url: str | None = None,
    *,
    keep_query_strings: bool = False,
) -> str | None:
    resolved = urljoin(base_url, url) if base_url else url
    resolved, _fragment = urldefrag(resolved)
    parsed = urlparse(resolved)
    scheme = parsed.scheme.lower()
    if scheme and scheme in DISALLOWED_SCHEMES:
        return None
    if scheme not in {"http", "https"}:
        return None

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    normalized = parsed._replace(
        scheme=scheme,
        netloc=parsed.netloc.lower(),
        path=path,
        params="",
        query=parsed.query if keep_query_strings else "",
        fragment="",
    )
    return urlunparse(normalized)


def is_same_origin(candidate: str, root: str) -> bool:
    c = urlparse(candidate)
    r = urlparse(root)
    return (c.scheme, c.netloc) == (r.scheme, r.netloc)
