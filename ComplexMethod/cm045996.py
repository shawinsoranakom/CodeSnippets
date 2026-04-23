def _render_visual_block_segments(block, para_block, img_buket_path='', table_enable=True):
    block_type = block['type']

    if block_type in [
        BlockType.IMAGE_CAPTION,
        BlockType.IMAGE_FOOTNOTE,
        BlockType.TABLE_CAPTION,
        BlockType.TABLE_FOOTNOTE,
        BlockType.CODE_CAPTION,
        BlockType.CODE_FOOTNOTE,
        BlockType.CHART_CAPTION,
        BlockType.CHART_FOOTNOTE,
    ]:
        block_text = merge_para_with_text(block)
        if block_text.strip():
            return [(block_text, 'markdown_line')]
        return []

    if block_type == BlockType.IMAGE_BODY:
        rendered_segments = []
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                if span.get('type') != ContentType.IMAGE:
                    continue
                rendered_segments.extend(
                    _build_visual_body_segments(
                        span.get('image_path', ''),
                        span.get('content', ''),
                        img_buket_path,
                        ContentType.IMAGE,
                        summary_override=para_block.get('sub_type', ''),
                    )
                )
        return rendered_segments

    if block_type == BlockType.CHART_BODY:
        rendered_segments = []
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                if span.get('type') != ContentType.CHART:
                    continue
                rendered_segments.extend(
                    _build_visual_body_segments(
                        span.get('image_path', ''),
                        span.get('content', ''),
                        img_buket_path,
                        ContentType.CHART,
                        summary_override=para_block.get('sub_type', ''),
                    )
                )
        return rendered_segments

    if block_type == BlockType.TABLE_BODY:
        rendered_segments = []
        for line in block.get('lines', []):
            for span in line.get('spans', []):
                if span.get('type') != ContentType.TABLE:
                    continue
                if table_enable and span.get('html', ''):
                    rendered_segments.append((
                        _format_embedded_html(span['html'], img_buket_path),
                        'html_block',
                    ))
                elif span.get('image_path', ''):
                    rendered_segments.append((
                        f"![]({_build_media_path(img_buket_path, span['image_path'])})",
                        'markdown_line',
                    ))
        return rendered_segments

    if block_type == BlockType.CODE_BODY:
        block_text = _render_code_block_markdown(block, para_block)
        if block_text.strip():
            return [(block_text, 'markdown_line')]
        return []

    return []