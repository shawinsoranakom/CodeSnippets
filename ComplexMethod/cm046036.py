def _join_rendered_span(para_block, block_lang, line, line_idx, span_idx, span_type, content):
    # 根据语言和上下文决定当前 span 后面的分隔符。
    # 这里集中处理：
    # 1. CJK 与西文的空格差异
    # 2. 西文行尾连字符是否需要跨行合并
    # 3. 独立公式是否作为块内容直接插入
    if span_type == ContentType.INTERLINE_EQUATION:
        return content, ''

    is_last_span = span_idx == len(line['spans']) - 1

    if block_lang in CJK_LANGS:
        if is_last_span and span_type != ContentType.INLINE_EQUATION:
            return content, ''
        return content, ' '

    if span_type not in [ContentType.TEXT, ContentType.INLINE_EQUATION]:
        return content, ''

    if (
        is_last_span
        and span_type == ContentType.TEXT
        and is_hyphen_at_line_end(content)
    ):
        if _next_line_starts_with_lowercase_text(para_block, line_idx):
            return content[:-1], ''
        return content, ''

    return content, ' '