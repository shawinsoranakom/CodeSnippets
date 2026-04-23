def _format_run_segment(
    seg: str,
    bold: bool,
    italic: bool,
    underline: bool,
    strikethrough: bool,
    script: str,
    url: str,
) -> str:
    """Apply Markdown/HTML inline formatting to a text segment."""
    t = seg
    if bold or italic or underline or strikethrough or script:
        leading = len(t) - len(t.lstrip())
        trailing = len(t) - len(t.rstrip())
        prefix = t[:leading] if leading else ""
        suffix = t[len(t) - trailing :] if trailing else ""
        inner = t.strip()
        if inner:
            if strikethrough:
                inner = f"~~{inner}~~"
            if bold and italic:
                inner = f"***{inner}***"
            elif bold:
                inner = f"**{inner}**"
            elif italic:
                inner = f"*{inner}*"
            if underline:
                inner = f"<u>{inner}</u>"
            if script == "super":
                inner = f"<sup>{inner}</sup>"
            elif script == "sub":
                inner = f"<sub>{inner}</sub>"
            t = prefix + inner + suffix
        elif underline and t:
            # Pure whitespace + underline = fill-in line
            # Replace spaces with NBSP so Markdown renderers preserve width
            t = "<u>" + "\u00a0" * len(t) + "</u>"
    if url:
        escaped_url = _escape_md_url(url)
        t = f"[{t}]({escaped_url})"
    return t