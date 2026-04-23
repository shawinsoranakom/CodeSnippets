def make_blocks_to_content_list(para_block, img_buket_path, page_idx, page_size):
    para_type = para_block['type']
    para_content = {}
    if para_type in [
        BlockType.TEXT,
        BlockType.REF_TEXT,
        BlockType.PHONETIC,
        BlockType.HEADER,
        BlockType.FOOTER,
        BlockType.PAGE_NUMBER,
        BlockType.ASIDE_TEXT,
        BlockType.PAGE_FOOTNOTE,
    ]:
        para_content = {
            'type': para_type,
            'text': merge_para_with_text(para_block),
        }
    elif para_type == BlockType.LIST:
        para_content = {
            'type': para_type,
            'sub_type': para_block.get('sub_type', ''),
            'list_items':[],
        }
        for block in para_block['blocks']:
            item_text = merge_para_with_text(block, escape_text_block_prefix=False)
            if item_text.strip():
                para_content['list_items'].append(item_text)
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
        para_content = {'type': ContentType.IMAGE, 'img_path': '', BlockType.IMAGE_CAPTION: [], BlockType.IMAGE_FOOTNOTE: []}
        image_path, _ = get_body_data(para_block)
        para_content['img_path'] = _build_media_path(img_buket_path, image_path)
        _apply_visual_sub_type(para_content, para_block)
        for block in para_block['blocks']:
            if block['type'] == BlockType.IMAGE_CAPTION:
                para_content[BlockType.IMAGE_CAPTION].append(merge_para_with_text(block))
            if block['type'] == BlockType.IMAGE_FOOTNOTE:
                para_content[BlockType.IMAGE_FOOTNOTE].append(merge_para_with_text(block))
    elif para_type == BlockType.TABLE:
        para_content = {'type': ContentType.TABLE, 'img_path': '', BlockType.TABLE_CAPTION: [], BlockType.TABLE_FOOTNOTE: []}
        for block in para_block['blocks']:
            if block['type'] == BlockType.TABLE_BODY:
                for line in block['lines']:
                    for span in line['spans']:
                        if span['type'] == ContentType.TABLE:

                            if span.get('html', ''):
                                para_content[BlockType.TABLE_BODY] = _format_embedded_html(
                                    span['html'],
                                    img_buket_path,
                                )

                            if span.get('image_path', ''):
                                para_content['img_path'] = f"{img_buket_path}/{span['image_path']}"

            if block['type'] == BlockType.TABLE_CAPTION:
                para_content[BlockType.TABLE_CAPTION].append(merge_para_with_text(block))
            if block['type'] == BlockType.TABLE_FOOTNOTE:
                para_content[BlockType.TABLE_FOOTNOTE].append(merge_para_with_text(block))
    elif para_type == BlockType.CHART:
        image_path, chart_content = get_body_data(para_block)
        para_content = {
            'type': ContentType.CHART,
            'img_path': _build_media_path(img_buket_path, image_path),
            'content': chart_content if chart_content else '',
            BlockType.CHART_CAPTION: [],
            BlockType.CHART_FOOTNOTE: [],
        }
        _apply_visual_sub_type(para_content, para_block)
        for block in para_block['blocks']:
            if block['type'] == BlockType.CHART_CAPTION:
                para_content[BlockType.CHART_CAPTION].append(merge_para_with_text(block))
            if block['type'] == BlockType.CHART_FOOTNOTE:
                para_content[BlockType.CHART_FOOTNOTE].append(merge_para_with_text(block))
    elif para_type == BlockType.CODE:
        para_content = {'type': BlockType.CODE, 'sub_type': para_block["sub_type"], BlockType.CODE_CAPTION: []}
        for block in para_block['blocks']:
            if block['type'] == BlockType.CODE_BODY:
                code_text = merge_para_with_text(block)
                if para_block['sub_type'] == BlockType.CODE:
                    guess_lang = para_block.get("guess_lang", "txt")
                    code_text = f"```{guess_lang}\n{code_text}\n```"
                para_content[BlockType.CODE_BODY] = code_text
            if block['type'] == BlockType.CODE_CAPTION:
                para_content[BlockType.CODE_CAPTION].append(merge_para_with_text(block))

    page_width, page_height = page_size
    para_bbox = para_block.get('bbox')
    if para_bbox:
        x0, y0, x1, y1 = para_bbox
        para_content['bbox'] = [
            int(x0 * 1000 / page_width),
            int(y0 * 1000 / page_height),
            int(x1 * 1000 / page_width),
            int(y1 * 1000 / page_height),
        ]

    para_content['page_idx'] = page_idx

    return para_content