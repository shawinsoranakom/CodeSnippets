def _runs_to_html(items) -> str:
    """Convert paragraph items to HTML inline text."""
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
        if bold:
            text = f"<b>{text}</b>"
        if italic:
            text = f"<i>{text}</i>"
        if underline:
            text = f"<u>{text}</u>"
        if strikethrough:
            text = f"<del>{text}</del>"
        if superscript:
            text = f"<sup>{text}</sup>"
        if subscript:
            text = f"<sub>{text}</sub>"
        if url:
            text = f'<a href="{url}">{text}</a>'
        parts.append(text)
    return "".join(parts)