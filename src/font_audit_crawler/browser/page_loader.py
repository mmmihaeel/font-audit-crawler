from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

from playwright.async_api import Browser, BrowserContext, Page, Request, ViewportSize
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from font_audit_crawler.constants import (
    DEFAULT_USER_AGENT,
    DEFAULT_VIEWPORTS,
    FONT_FILE_EXTENSIONS,
)
from font_audit_crawler.extract.text_nodes import build_runtime_probe_script
from font_audit_crawler.models.runtime import (
    FontRequest,
    PageRuntimeSnapshot,
    RuntimeFontFaceRule,
    RuntimeTextElement,
)


@dataclass
class LoadedPage:
    context: BrowserContext
    page: Page
    snapshot: PageRuntimeSnapshot


KNOWN_OVERLAY_SELECTORS = [
    "#onetrust-reject-all-handler",
    "#onetrust-accept-btn-handler",
    "#onetrust-close-btn-container button",
    "#onetrust-pc-btn-handler",
    "#truste-consent-button",
    "button[aria-label='Close']",
    "button[aria-label='close']",
]

OVERLAY_CONTAINER_SELECTORS = [
    "[id*='cookie']",
    "[class*='cookie']",
    "[id*='consent']",
    "[class*='consent']",
    "[id*='onetrust']",
    "[class*='onetrust']",
    "[id*='trustarc']",
    "[class*='trustarc']",
    "[role='dialog']",
    "[aria-modal='true']",
]

OVERLAY_ACTION_TOKEN_GROUPS = [
    [
        "reject",
        "decline",
        "deny",
        "odrzu",
        "essential only",
        "only necessary",
        "alles ablehnen",
        "tout refuser",
        "rechazar",
    ],
    [
        "close",
        "dismiss",
        "zamknij",
        "cerrar",
        "\u9589\u3058\u308b",
    ],
    [
        "accept",
        "agree",
        "allow",
        "continue",
        "enter",
        "akcept",
        "zgadz",
        "acept",
        "\u540c\u610f",
        "\u627f\u8afe",
        "\u7d9a\u3051\u308b",
        "i understand",
    ],
]


def _is_font_request(request: Request) -> bool:
    return request.resource_type == "font" or request.url.lower().endswith(FONT_FILE_EXTENSIONS)


async def _click_known_overlay_controls(page: Page) -> bool:
    for selector in KNOWN_OVERLAY_SELECTORS:
        locator = page.locator(selector).first
        if await locator.count() == 0 or not await locator.is_visible():
            continue
        try:
            await locator.click(timeout=1_500)
        except Exception:
            continue
        await page.wait_for_timeout(600)
        return True
    return False


async def _dismiss_overlay_by_text(page: Page) -> bool:
    payload = await page.evaluate(
        """
        ({ containerSelectors, tokenGroups }) => {
          const normalize = (value) => (value || "").toLowerCase().replace(/\\s+/g, " ").trim();
          const selectors = containerSelectors.join(",");
          const containers = Array.from(document.querySelectorAll(selectors)).filter((el) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return (
              rect.width > 0 &&
              rect.height > 0 &&
              style.display !== "none" &&
              style.visibility !== "hidden"
            );
          });

          for (const tokens of tokenGroups) {
            for (const container of containers.slice(0, 20)) {
              const buttons = Array.from(
                container.querySelectorAll(
                  "button, a, [role='button'], input[type='button'], input[type='submit']"
                )
              );
              for (const button of buttons) {
                const text = normalize(
                  button.innerText ||
                  button.textContent ||
                  button.value ||
                  button.getAttribute("aria-label") ||
                  ""
                );
                if (!text) {
                  continue;
                }
                if (tokens.some((token) => text.includes(token))) {
                  button.click();
                  return { clicked: true, text };
                }
              }
            }
          }
          return { clicked: false, text: null };
        }
        """,
        {
            "containerSelectors": OVERLAY_CONTAINER_SELECTORS,
            "tokenGroups": OVERLAY_ACTION_TOKEN_GROUPS,
        },
    )
    if payload.get("clicked"):
        await page.wait_for_timeout(600)
        return True
    return False


async def dismiss_obstructive_overlays(page: Page) -> None:
    for _attempt in range(3):
        clicked = await _click_known_overlay_controls(page)
        if not clicked:
            clicked = await _dismiss_overlay_by_text(page)
        if not clicked:
            return
        with suppress(PlaywrightTimeoutError):
            await page.wait_for_load_state("networkidle", timeout=2_000)


@asynccontextmanager
async def open_page_snapshot(
    browser: Browser,
    url: str,
    *,
    viewport_name: str,
    timeout_ms: int,
    wait_after_load_ms: int,
    max_elements_per_page: int,
) -> AsyncIterator[LoadedPage]:
    site_origin = urlparse(url).netloc.lower()
    context = await browser.new_context(
        viewport=cast(ViewportSize, DEFAULT_VIEWPORTS[viewport_name]),
        user_agent=DEFAULT_USER_AGENT,
    )
    page = await context.new_page()
    font_requests: list[FontRequest] = []

    def _track_request(request: Request) -> None:
        if not _is_font_request(request):
            return
        font_requests.append(
            FontRequest(
                url=request.url,
                resource_type=request.resource_type,
                same_origin=urlparse(request.url).netloc.lower() == site_origin,
            )
        )

    page.on("request", _track_request)

    snapshot = PageRuntimeSnapshot(url=url, viewport=viewport_name)
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        with suppress(PlaywrightTimeoutError):
            await page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 2_500))
        if wait_after_load_ms:
            await page.wait_for_timeout(wait_after_load_ms)
        await dismiss_obstructive_overlays(page)
        await page.evaluate(
            "() => document.fonts ? document.fonts.ready.then(() => true) : Promise.resolve(true)"
        )
        raw_payload = await page.evaluate(build_runtime_probe_script(max_elements_per_page))
        snapshot = PageRuntimeSnapshot(
            url=url,
            viewport=viewport_name,
            elements=[
                RuntimeTextElement.model_validate(item) for item in raw_payload.get("elements", [])
            ],
            font_face_rules=[
                RuntimeFontFaceRule.model_validate(item)
                for item in raw_payload.get("font_faces", [])
            ],
            font_requests=font_requests,
        )
        yield LoadedPage(context=context, page=page, snapshot=snapshot)
    except Exception as exc:
        yield LoadedPage(
            context=context,
            page=page,
            snapshot=PageRuntimeSnapshot(
                url=url,
                viewport=viewport_name,
                font_requests=font_requests,
                page_error=str(exc),
            ),
        )
    finally:
        await context.close()


async def capture_page_screenshot(page: Page, target: Path) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(target), full_page=True)
    return str(target)
