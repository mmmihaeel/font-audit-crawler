from __future__ import annotations

import fnmatch
import re
from urllib.parse import urlparse


def matches_pattern(url: str, pattern: str) -> bool:
    if pattern.startswith("re:"):
        return re.search(pattern[3:], url) is not None
    parsed = urlparse(url)
    return fnmatch.fnmatch(url, pattern) or fnmatch.fnmatch(parsed.path or "/", pattern)


def matches_patterns(url: str, patterns: list[str]) -> bool:
    return any(matches_pattern(url, pattern) for pattern in patterns)


def should_visit(url: str, include: list[str], exclude: list[str]) -> bool:
    if include and not matches_patterns(url, include):
        return False
    return not (exclude and matches_patterns(url, exclude))
