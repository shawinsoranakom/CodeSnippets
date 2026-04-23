def merge_para_with_text_v2(para_block):
    block_lang = detect_lang(_collect_text_for_lang_detection(para_block))
    para_content = []
    para_type = para_block.get('type')

    for line_idx, line in enumerate(para_block.get('lines', [])):
        for span_idx, span in enumerate(line.get('spans', [])):
            span_type = span.get('type')

            if span_type == ContentType.TEXT:
                content = _normalize_text_content(span.get('content', ''))
                if not content.strip():
                    continue

                output_type = (
                    ContentTypeV2.SPAN_PHONETIC
                    if para_type == BlockType.PHONETIC
                    else ContentTypeV2.SPAN_TEXT
                )
                is_last_span = span_idx == len(line['spans']) - 1

                if block_lang in CJK_LANGS:
                    rendered_content = content if is_last_span else f"{content} "
                else:
                    if (
                        is_last_span
                        and is_hyphen_at_line_end(content)
                        and _next_line_starts_with_lowercase_text(para_block, line_idx)
                    ):
                        rendered_content = content[:-1]
                    elif is_last_span and is_hyphen_at_line_end(content):
                        rendered_content = content
                    else:
                        rendered_content = f"{content} "

                if para_content and para_content[-1]['type'] == output_type:
                    para_content[-1]['content'] += rendered_content
                else:
                    para_content.append({
                        'type': output_type,
                        'content': rendered_content,
                    })
            elif span_type == ContentType.INLINE_EQUATION:
                content = span.get('content', '').strip()
                if content:
                    para_content.append({
                        'type': ContentTypeV2.SPAN_EQUATION_INLINE,
                        'content': content,
                    })

    if para_content and para_content[-1]['type'] in [
        ContentTypeV2.SPAN_TEXT,
        ContentTypeV2.SPAN_PHONETIC,
    ]:
        para_content[-1]['content'] = para_content[-1]['content'].rstrip()

    return para_content