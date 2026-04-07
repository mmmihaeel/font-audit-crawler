DEFAULT_USER_AGENT = "font-audit-crawler/0.1 (+https://github.com/mmmihaeel/font-audit-crawler)"
FONT_FILE_EXTENSIONS = (".woff", ".woff2", ".ttf", ".otf")
DEFAULT_VIEWPORTS: dict[str, dict[str, int]] = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}
