from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from font_audit_crawler.config import load_app_config, load_rules_bundle
from font_audit_crawler.logging import configure_logging
from font_audit_crawler.models.config_models import (
    AppConfig,
    FailOnSeverity,
    ScreenshotMode,
    SitemapMode,
    ViewportMode,
)
from font_audit_crawler.reporting.html_report import write_html_report
from font_audit_crawler.reporting.json_report import write_json_report
from font_audit_crawler.reporting.markdown_report import write_markdown_report
from font_audit_crawler.scanner import run_scan
from font_audit_crawler.utils.fonts import choose_exit_code
from font_audit_crawler.utils.paths import make_output_dir

app = typer.Typer(help="Deterministic runtime font compliance auditor.")
console = Console()


def _apply_cli_overrides(
    config_path: Path | None,
    *,
    rules_path: Path | None,
    max_pages: int | None,
    max_depth: int | None,
    timeout_ms: int | None,
    max_page_bytes: int | None,
    max_sitemap_bytes: int | None,
    include: list[str] | None,
    exclude: list[str] | None,
    viewport: ViewportMode | None,
    screenshot: ScreenshotMode | None,
    sitemap: SitemapMode | None,
    fail_on: FailOnSeverity | None,
) -> tuple[Path | None, AppConfig]:
    app_config = load_app_config(config_path)
    if rules_path is not None:
        app_config.rules_path = rules_path.resolve()
    if max_pages is not None:
        app_config.scan.max_pages = max_pages
    if max_depth is not None:
        app_config.scan.max_depth = max_depth
    if timeout_ms is not None:
        app_config.scan.timeout_ms = timeout_ms
    if max_page_bytes is not None:
        app_config.scan.max_page_bytes = max_page_bytes
    if max_sitemap_bytes is not None:
        app_config.scan.max_sitemap_bytes = max_sitemap_bytes
    if include:
        app_config.scan.include = include
    if exclude:
        app_config.scan.exclude = exclude
    if viewport is not None:
        app_config.scan.viewport = viewport
    if screenshot is not None:
        app_config.scan.screenshot = screenshot
    if sitemap is not None:
        app_config.scan.sitemap = sitemap
    if fail_on is not None:
        app_config.scan.fail_on = fail_on
    return config_path, app_config


@app.command()
def scan(
    url: Annotated[str, typer.Option("--url", help="Root URL to scan.")],
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Output directory root."),
    ] = None,
    rules: Annotated[
        Path | None,
        typer.Option("--rules", help="Rules override file or directory."),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", help="Optional YAML config file."),
    ] = None,
    max_pages: Annotated[
        int | None,
        typer.Option("--max-pages", help="Maximum number of pages to visit."),
    ] = None,
    max_depth: Annotated[
        int | None,
        typer.Option("--max-depth", help="Maximum crawl depth."),
    ] = None,
    timeout_ms: Annotated[
        int | None,
        typer.Option("--timeout-ms", help="Per-page timeout in milliseconds."),
    ] = None,
    max_page_bytes: Annotated[
        int | None,
        typer.Option("--max-page-bytes", help="Maximum bytes to read for a crawl HTML page."),
    ] = None,
    max_sitemap_bytes: Annotated[
        int | None,
        typer.Option("--max-sitemap-bytes", help="Maximum bytes to read for sitemap discovery."),
    ] = None,
    include: Annotated[
        list[str] | None,
        typer.Option("--include", help="Include URL glob or re:pattern."),
    ] = None,
    exclude: Annotated[
        list[str] | None,
        typer.Option("--exclude", help="Exclude URL glob or re:pattern."),
    ] = None,
    viewport: Annotated[
        ViewportMode | None,
        typer.Option("--viewport", help="Viewport to scan."),
    ] = None,
    screenshot: Annotated[
        ScreenshotMode | None,
        typer.Option(
            "--screenshot",
            help="Capture no screenshots, page screenshots, or finding screenshots.",
        ),
    ] = None,
    sitemap: Annotated[
        SitemapMode | None,
        typer.Option("--sitemap", help="Sitemap discovery mode."),
    ] = None,
    fail_on: Annotated[
        FailOnSeverity | None,
        typer.Option(
            "--fail-on",
            help="Exit non-zero when findings reach this severity threshold.",
        ),
    ] = None,
    verbose: Annotated[bool, typer.Option("--verbose", help="Enable verbose logging.")] = False,
) -> None:
    configure_logging(verbose)
    _, app_config = _apply_cli_overrides(
        config,
        rules_path=rules,
        max_pages=max_pages,
        max_depth=max_depth,
        timeout_ms=timeout_ms,
        max_page_bytes=max_page_bytes,
        max_sitemap_bytes=max_sitemap_bytes,
        include=include,
        exclude=exclude,
        viewport=viewport,
        screenshot=screenshot,
        sitemap=sitemap,
        fail_on=fail_on,
    )
    output_dir = make_output_dir(output, url)
    console.print(f"[bold green]Output:[/bold green] {output_dir}")

    report = asyncio.run(run_scan(start_url=url, config=app_config, output_dir=output_dir))

    artifact_paths = {
        "json": output_dir / "report.json",
        "markdown": output_dir / "report.md",
        "html": output_dir / "report.html",
    }
    requested_formats = {item.value for item in app_config.scan.output_formats}
    if "json" in requested_formats:
        write_json_report(artifact_paths["json"], report)
    if "markdown" in requested_formats:
        write_markdown_report(artifact_paths["markdown"], report)
    if "html" in requested_formats:
        write_html_report(artifact_paths["html"], report)
    (output_dir / "artifacts" / "crawl-urls.txt").write_text(
        "\n".join(report.scanned_urls),
        encoding="utf-8",
    )

    table = Table(title="Scan Summary")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Scanned pages", str(report.summary.scanned_pages))
    table.add_row("Successful pages", str(report.summary.successful_pages))
    table.add_row("Total findings", str(report.summary.findings_total))
    table.add_row("By severity", str(report.summary.findings_by_severity))
    table.add_row("By type", str(report.summary.findings_by_type))
    console.print(table)

    if report.head_requirements.required_families:
        console.print(
            "[bold]Required approved families:[/bold] "
            + ", ".join(report.head_requirements.required_families)
        )

    exit_code = choose_exit_code(
        [finding.severity for finding in report.findings],
        app_config.scan.fail_on,
    )
    raise typer.Exit(code=exit_code)


@app.command("validate-config")
def validate_config(
    config: Annotated[Path, typer.Option("--config", exists=True, readable=True)],
) -> None:
    _ = load_app_config(config)
    console.print("[green]Config is valid.[/green]")


@app.command("list-rules")
def list_rules(
    rules_path: Annotated[
        Path | None,
        typer.Option("--rules", help="Optional rules override file or directory."),
    ] = None,
) -> None:
    rules = load_rules_bundle(rules_path)
    table = Table(title="Bundled Rules")
    table.add_column("Section")
    table.add_column("Summary")
    table.add_row("Approved", ", ".join(item.name for item in rules.approved.approved_families))
    table.add_row("Mappings", str(len(rules.mappings.explicit_mappings)))
    table.add_row("Fallbacks", str(len(rules.fallbacks.disallowed_fallbacks)))
    table.add_row("Vendors", str(len(rules.vendors.vendor_font_exceptions)))
    table.add_row("Locale", str(len(rules.locale.locale_fallbacks)))
    console.print(table)


@app.command()
def doctor() -> None:
    console.print("[bold]Environment checks[/bold]")
    try:
        import playwright  # noqa: F401

        console.print("[green]Playwright package import: OK[/green]")
    except Exception as exc:
        console.print(f"[red]Playwright package import failed:[/red] {exc}")
    console.print("Remember to run: [cyan]uv run playwright install chromium[/cyan]")
