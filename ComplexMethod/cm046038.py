def make_blocks_to_content_list(para_block, img_buket_path, page_idx, page_size):
    para_type = para_block['type']
    para_content = None
    if para_type in [
        BlockType.TEXT,
        BlockType.INDEX,
        BlockType.LIST,
        BlockType.ABSTRACT,
    ]:
        para_content = {
            'type': ContentType.TEXT,
            'text': merge_para_with_text(para_block),
        }
    elif para_type in [
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
    elif para_type == BlockType.REF_TEXT:
        para_content = {
            'type': BlockType.LIST,
            'sub_type': BlockType.REF_TEXT,
            'list_items': [],
        }
        for block in _get_ref_text_item_blocks(para_block):
            item_text = merge_para_with_text(block)
            if item_text.strip():
                para_content['list_items'].append(item_text)
    elif para_type == BlockType.TITLE:
        para_content = {
            'type': ContentType.TEXT,
            'text': merge_para_with_text(para_block),
        }
        title_level = get_title_level(para_block)
        if title_level != 0:
            para_content['text_level'] = title_level
    elif para_type == BlockType.INTERLINE_EQUATION:
        if len(para_block['lines']) == 0 or len(para_block['lines'][0]['spans']) == 0:
            return None
        para_content = {
            'type': ContentType.EQUATION,
            'img_path': f"{img_buket_path}/{para_block['lines'][0]['spans'][0].get('image_path', '')}",
        }
        if para_block['lines'][0]['spans'][0].get('content', ''):
            para_content['text'] = merge_para_with_text(para_block)
            para_content['text_format'] = 'latex'
    elif para_type == BlockType.SEAL:
        seal_span = _get_seal_span(para_block)
        if not seal_span:
            return None
        para_content = {
            'type': ContentType.SEAL,
            'img_path': f"{img_buket_path}/{seal_span.get('image_path', '')}",
            'text': _get_seal_text(para_block),
        }
    elif para_type == BlockType.IMAGE:
        para_content = {'type': ContentType.IMAGE, 'img_path': '', BlockType.IMAGE_CAPTION: [], BlockType.IMAGE_FOOTNOTE: []}
        for block in para_block['blocks']:
            if block['type'] == BlockType.IMAGE_BODY:
                for line in block['lines']:
                    for span in line['spans']:
                        if span['type'] == ContentType.IMAGE:
                            if span.get('image_path', ''):
                                para_content['img_path'] = f"{img_buket_path}/{span['image_path']}"
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
        para_content = {
            'type': ContentType.CHART,
            'img_path': '',
            'content': '',
            BlockType.CHART_CAPTION: [],
            BlockType.CHART_FOOTNOTE: [],
        }
        for block in para_block.get('blocks', []):
            if block['type'] == BlockType.CHART_BODY:
                for line in block['lines']:
                    for span in line['spans']:
                        if span['type'] == ContentType.CHART and span.get('image_path', ''):
                            para_content['img_path'] = f"{img_buket_path}/{span['image_path']}"
            if block['type'] == BlockType.CHART_CAPTION:
                para_content[BlockType.CHART_CAPTION].append(merge_para_with_text(block))
            if block['type'] == BlockType.CHART_FOOTNOTE:
                para_content[BlockType.CHART_FOOTNOTE].append(merge_para_with_text(block))
    elif para_type == BlockType.CODE:
        para_content = {
            'type': BlockType.CODE,
            'sub_type': para_block['sub_type'],
            BlockType.CODE_CAPTION: [],
            BlockType.CODE_FOOTNOTE: [],
        }
        for block in para_block.get('blocks', []):
            render_block = _inherit_parent_code_render_metadata(block, para_block)
            if block['type'] == BlockType.CODE_BODY:
                para_content[BlockType.CODE_BODY] = merge_para_with_text(render_block)
            if block['type'] == BlockType.CODE_CAPTION:
                para_content[BlockType.CODE_CAPTION].append(merge_para_with_text(block))
            if block['type'] == BlockType.CODE_FOOTNOTE:
                para_content[BlockType.CODE_FOOTNOTE].append(merge_para_with_text(block))

    if not para_content:
        return None

    bbox = _build_bbox(para_block.get('bbox'), page_size)
    if bbox:
        para_content['bbox'] = bbox
    para_content['page_idx'] = page_idx

    return para_content