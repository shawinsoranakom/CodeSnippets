def _apply_html_style(content: str, style: list) -> str:
    """Apply inline styles with HTML tags for markdown-hostile contexts."""
    if not style or not content:
        return content

    if 'bold' in style and 'italic' in style:
        content = f'<strong><em>{content}</em></strong>'
    elif 'bold' in style:
        content = f'<strong>{content}</strong>'
    elif 'italic' in style:
        content = f'<em>{content}</em>'

    if 'strikethrough' in style:
        content = f'<del>{content}</del>'

    if 'underline' in style:
        content = f'<u>{content}</u>'

    return content