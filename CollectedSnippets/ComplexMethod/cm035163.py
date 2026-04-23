def _runs_to_markdown(items) -> str:
    """Convert paragraph items to Markdown inline text, merging adjacent items with identical formatting."""
    parts = []
    for (
        bold,
        italic,
        underline,
        strikethrough,
        superscript,
        subscript,
        text,
        url,
    ) in _merge_runs(items):
        if bold or italic or underline or strikethrough or superscript or subscript:
            # CommonMark: marker characters must not be surrounded by spaces
            leading = len(text) - len(text.lstrip())
            trailing = len(text) - len(text.rstrip())
            prefix = text[:leading] if leading else ""
            suffix = text[len(text) - trailing :] if trailing else ""
            inner = text.strip()
            if inner:
                # Apply strikethrough first (innermost)
                if strikethrough:
                    inner = f"~~{inner}~~"
                # Apply bold/italic
                if bold and italic:
                    inner = f"***{inner}***"
                elif bold:
                    inner = f"**{inner}**"
                elif italic:
                    inner = f"*{inner}*"
                # Apply underline
                if underline:
                    inner = f"<u>{inner}</u>"
                # Apply superscript/subscript (outermost)
                if superscript:
                    inner = f"<sup>{inner}</sup>"
                elif subscript:
                    inner = f"<sub>{inner}</sub>"
                text = prefix + inner + suffix
            elif underline and text:
                # Pure whitespace + underline = fill-in line (e.g. "作者姓名：___")
                # Replace spaces with NBSP so Markdown renderers preserve width
                text = "<u>" + "\u00a0" * len(text) + "</u>"
        if url:
            text = f"[{text}]({_escape_md_url(url)})"
        parts.append(text)
    # Prevent bold/italic/strikethrough markers from merging with adjacent alphanumeric text (CommonMark requirement)
    result = []
    for i, part in enumerate(parts):
        if i > 0 and result:
            prev = result[-1]
            # Previous part ends with closing marker and current part starts with alphanumeric
            if prev.endswith(("**", "*", "~~")) and part and part[0].isalnum():
                result.append("\u200b")
        result.append(part)
    return "".join(result)