def merge_para_with_text_v2(para_block):
    _visible_styles = {'underline', 'strikethrough'}
    para_content = []
    for i, line in enumerate(para_block['lines']):
        for j, span in enumerate(line['spans']):
            content = span.get("content", '')
            span_style = span.get('style', [])
            has_visible_style = bool(
                span_style and any(s in _visible_styles for s in span_style)
            )
            if content.strip() or (content and has_visible_style):
                if span['type'] == ContentType.INLINE_EQUATION:
                    span['type'] = ContentTypeV2.SPAN_EQUATION_INLINE
                para_content.append(span)
    return para_content