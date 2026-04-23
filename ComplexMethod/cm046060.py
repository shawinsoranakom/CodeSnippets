def merge_para_with_text(para_block, escape_text_block_prefix=True):
    # First pass: collect rendered parts with raw boundary metadata.
    parts = []
    if para_block['type'] == BlockType.TITLE:
        if para_block.get('is_numbered_style', False):
            section_number = para_block.get('section_number', '')
            if section_number:
                parts.append(
                    _make_rendered_part(
                        ContentType.TEXT,
                        f"{section_number} ",
                        raw_content=f"{section_number} ",
                    )
                )

    for line in para_block['lines']:
        for span in line['spans']:
            span_type = span['type']
            span_style = span.get('style', [])

            if span_type == ContentType.TEXT:
                _append_text_part(parts, span['content'], span_style)
            elif span_type == ContentType.INLINE_EQUATION:
                content = f"{inline_left_delimiter}{span['content']}{inline_right_delimiter}"
                content = content.strip()
                if content:
                    parts.append(
                        _make_rendered_part(
                            span_type,
                            content,
                            raw_content=span['content'],
                        )
                    )
            elif span_type == ContentType.INTERLINE_EQUATION:
                content = f"\n{display_left_delimiter}\n{span['content']}\n{display_right_delimiter}\n"
                content = content.strip()
                if content:
                    parts.append(
                        _make_rendered_part(
                            span_type,
                            content,
                            raw_content=span['content'],
                        )
                    )
            elif span_type == ContentType.HYPERLINK:
                _append_hyperlink_part(
                    parts,
                    span['content'],
                    span_style,
                    url=span.get('url', ''),
                )

    para_text = _join_rendered_parts(parts)
    if escape_text_block_prefix and para_block.get('type') == BlockType.TEXT:
        para_text = escape_text_block_markdown_prefix(para_text)
    return para_text