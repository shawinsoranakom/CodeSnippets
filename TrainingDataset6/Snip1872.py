def extract_markdown_links(lines: list[str]) -> list[MarkdownLinkInfo]:
    """
    Extract all markdown links from the given lines.

    Return list of MarkdownLinkInfo, where each dict contains:
    - `line_no` - line number (1-based)
    - `url` - link URL
    - `text` - link text
    - `title` - link title (if any)
    """

    links: list[MarkdownLinkInfo] = []
    for line_no, line in enumerate(lines, start=1):
        for m in MARKDOWN_LINK_RE.finditer(line):
            links.append(
                MarkdownLinkInfo(
                    line_no=line_no,
                    url=m.group("url"),
                    text=m.group("text"),
                    title=m.group("title"),
                    attributes=m.group("attrs"),
                    full_match=m.group(0),
                )
            )
    return links