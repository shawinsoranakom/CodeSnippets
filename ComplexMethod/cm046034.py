def render_visual_block_segments(block, img_buket_path=''):
    # 将单个视觉子 block 渲染成一个或多个 segment。
    # 文本类子块统一输出 markdown_line；
    # table 的 html 输出为 html_block，供后续决定是否需要空行隔开。
    block_type = block['type']

    if block_type in [
        BlockType.IMAGE_CAPTION,
        BlockType.IMAGE_FOOTNOTE,
        BlockType.TABLE_CAPTION,
        BlockType.TABLE_FOOTNOTE,
        BlockType.CODE_BODY,
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
        return [
            (f"![]({img_buket_path}/{span['image_path']})", 'markdown_line')
            for line in block['lines']
            for span in line['spans']
            if span['type'] == ContentType.IMAGE and span.get('image_path', '')
        ]

    if block_type == BlockType.CHART_BODY:
        return [
            (f"![]({img_buket_path}/{span['image_path']})", 'markdown_line')
            for line in block['lines']
            for span in line['spans']
            if span['type'] == ContentType.CHART and span.get('image_path', '')
        ]

    if block_type == BlockType.TABLE_BODY:
        rendered_segments = []
        for line in block['lines']:
            for span in line['spans']:
                if span['type'] != ContentType.TABLE:
                    continue
                if span.get('html', ''):
                    rendered_segments.append((
                        _format_embedded_html(span['html'], img_buket_path),
                        'html_block',
                    ))
                elif span.get('image_path', ''):
                    rendered_segments.append((f"![]({img_buket_path}/{span['image_path']})", 'markdown_line'))
        return rendered_segments

    return []