def _needs_markdown_it_boundary_space(prev_part: dict, next_part: dict) -> bool:
    if _get_office_style_render_mode() != OFFICE_STYLE_RENDER_MODE_MARKDOWN:
        return False
    if not prev_part.get('has_markdown_wrapper', False):
        return False
    if next_part.get('span_type') in {
        ContentType.HYPERLINK,
        ContentType.INLINE_EQUATION,
        ContentType.INTERLINE_EQUATION,
    }:
        return False

    prev_raw = prev_part.get('raw_content', '')
    next_raw = next_part.get('raw_content', '')
    if not prev_raw.strip() or not next_raw.strip():
        return False
    if prev_raw[-1].isspace() or next_raw[0].isspace():
        return False

    prev_char = _get_last_non_whitespace_char(prev_raw)
    next_char = _get_first_non_whitespace_char(next_raw)
    if prev_char is None or next_char is None:
        return False
    if not _is_punctuation_or_symbol(prev_char):
        return False
    if not _is_boundary_text_char(next_char):
        return False
    return True