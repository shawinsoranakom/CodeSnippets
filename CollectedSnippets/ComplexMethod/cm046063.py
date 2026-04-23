def make_blocks_to_content_list(para_block, img_buket_path, page_idx):
    para_type = para_block['type']
    para_content = {}
    if para_type in [
        BlockType.TEXT,
        BlockType.HEADER,
        BlockType.FOOTER,
        BlockType.PAGE_FOOTNOTE,
    ]:
        para_content = {
            'type': para_type,
            'text': merge_para_with_text(para_block),
        }
    elif para_type == BlockType.LIST:
        attribute = para_block.get('attribute', 'unordered')
        para_content = {
            'type': para_type,
            'list_items': _flatten_list_items(para_block),
        }
    elif para_type == BlockType.INDEX:
        para_content = {
            'type': para_type,
            'list_items': _flatten_index_items(para_block),
        }
    elif para_type == BlockType.TITLE:
        title_level = get_title_level(para_block)
        para_content = {
            'type': ContentType.TEXT,
            'text': merge_para_with_text(para_block),
        }
        if title_level != 0:
            para_content['text_level'] = title_level
    elif para_type == BlockType.INTERLINE_EQUATION:
        para_content = {
            'type': ContentType.EQUATION,
            'text': merge_para_with_text(para_block),
            'text_format': 'latex',
        }
    elif para_type == BlockType.IMAGE:
        para_content = {'type': ContentType.IMAGE, 'img_path': '', BlockType.IMAGE_CAPTION: []}
        for block in para_block['blocks']:
            if block['type'] == BlockType.IMAGE_BODY:
                for line in block['lines']:
                    for span in line['spans']:
                        if span['type'] == ContentType.IMAGE:
                            if span.get('image_path', ''):
                                para_content['img_path'] = f"{img_buket_path}/{span['image_path']}"
            if block['type'] == BlockType.IMAGE_CAPTION:
                para_content[BlockType.IMAGE_CAPTION].append(merge_para_with_text(block))
    elif para_type == BlockType.TABLE:
        para_content = {'type': ContentType.TABLE, BlockType.TABLE_CAPTION: []}
        for block in para_block['blocks']:
            if block['type'] == BlockType.TABLE_BODY:
                for line in block['lines']:
                    for span in line['spans']:
                        if span['type'] == ContentType.TABLE:
                            if span.get('html', ''):
                                para_content[BlockType.TABLE_BODY] = _format_embedded_html(span['html'], img_buket_path)
            if block['type'] == BlockType.TABLE_CAPTION:
                para_content[BlockType.TABLE_CAPTION].append(merge_para_with_text(block))
    elif para_type == BlockType.CHART:
        para_content = {
            'type': ContentType.CHART,
            'img_path': '',
            'content': '',
            BlockType.CHART_CAPTION: [],
        }
        for block in para_block['blocks']:
            if block['type'] == BlockType.CHART_BODY:
                for line in block['lines']:
                    for span in line['spans']:
                        if span['type'] == ContentType.CHART:
                            para_content['img_path'] = _build_media_path(
                                img_buket_path,
                                span.get('image_path', ''),
                            )
                            if span.get('content', ''):
                                para_content['content'] = _format_embedded_html(
                                    span['content'],
                                    img_buket_path,
                                )
            if block['type'] == BlockType.CHART_CAPTION:
                para_content[BlockType.CHART_CAPTION].append(merge_para_with_text(block))

    para_content['page_idx'] = page_idx
    anchor = para_block.get("anchor")
    if isinstance(anchor, str) and anchor.strip():
        para_content["anchor"] = anchor.strip()

    return para_content