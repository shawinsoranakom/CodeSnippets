def _join_rendered_parts(parts: list[dict]) -> str:
    para_text = ''
    prev_part = None

    for i, part in enumerate(parts):
        span_type = part['span_type']
        content = part['rendered_content']
        is_last = i == len(parts) - 1

        if span_type == ContentType.INLINE_EQUATION:
            if para_text and not para_text.endswith(' '):
                para_text += ' '
            para_text += content
            if not is_last:
                para_text += ' '
        else:
            if prev_part is not None and _needs_markdown_it_boundary_space(prev_part, part):
                para_text += ' '
            para_text += content

        prev_part = part

    return para_text