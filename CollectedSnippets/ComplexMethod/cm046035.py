def _render_span(span, escape_markdown=True):
    # 将单个 span 渲染成 markdown 片段。
    # 这里只负责“渲染成什么文本”，不决定后面是否补空格。
    span_type = span['type']
    content = ''

    if span_type == ContentType.TEXT:
        content = _normalize_text_content(span.get('content', ''))
        if escape_markdown:
            content = escape_special_markdown_char(content)
    elif span_type == ContentType.INLINE_EQUATION:
        if span.get('content', ''):
            content = f"{inline_left_delimiter}{span['content']}{inline_right_delimiter}"
    elif span_type == ContentType.INTERLINE_EQUATION:
        if span.get('content', ''):
            content = f"\n{display_left_delimiter}\n{span['content']}\n{display_right_delimiter}\n"
    else:
        return None

    content = content.strip()
    if not content:
        return None

    return span_type, content