def make_blocks_to_content_list_v2(para_block, img_buket_path, page_size):
    para_type = para_block['type']
    para_content = None

    if para_type in [
        BlockType.HEADER,
        BlockType.FOOTER,
        BlockType.ASIDE_TEXT,
        BlockType.PAGE_NUMBER,
        BlockType.PAGE_FOOTNOTE,
    ]:
        if para_type == BlockType.HEADER:
            content_type = ContentTypeV2.PAGE_HEADER
        elif para_type == BlockType.FOOTER:
            content_type = ContentTypeV2.PAGE_FOOTER
        elif para_type == BlockType.ASIDE_TEXT:
            content_type = ContentTypeV2.PAGE_ASIDE_TEXT
        elif para_type == BlockType.PAGE_NUMBER:
            content_type = ContentTypeV2.PAGE_NUMBER
        elif para_type == BlockType.PAGE_FOOTNOTE:
            content_type = ContentTypeV2.PAGE_FOOTNOTE
        else:
            raise ValueError(f"Unknown para_type: {para_type}")
        para_content = {
            'type': content_type,
            'content': {
                f"{content_type}_content": merge_para_with_text_v2(para_block),
            },
        }
    elif para_type == BlockType.TITLE:
        title_level = get_title_level(para_block)
        if title_level != 0:
            para_content = {
                'type': ContentTypeV2.TITLE,
                'content': {
                    'title_content': merge_para_with_text_v2(para_block),
                    'level': title_level,
                },
            }
        else:
            para_content = {
                'type': ContentTypeV2.PARAGRAPH,
                'content': {
                    'paragraph_content': merge_para_with_text_v2(para_block),
                },
            }
    elif para_type in [
        BlockType.TEXT,
        BlockType.ABSTRACT,
    ]:
        para_content = {
            'type': ContentTypeV2.PARAGRAPH,
            'content': {
                'paragraph_content': merge_para_with_text_v2(para_block),
            },
        }
    elif para_type == BlockType.INTERLINE_EQUATION:
        image_path, math_content = _get_body_data(para_block)
        para_content = {
            'type': ContentTypeV2.EQUATION_INTERLINE,
            'content': {
                'math_content': math_content,
                'math_type': 'latex',
                'image_source': {'path': f"{img_buket_path}/{image_path}"},
            },
        }
    elif para_type == BlockType.IMAGE:
        image_caption = []
        image_footnote = []
        image_path, _ = _get_body_data(para_block)
        for block in para_block.get('blocks', []):
            if block['type'] == BlockType.IMAGE_CAPTION:
                image_caption.extend(merge_para_with_text_v2(block))
            if block['type'] == BlockType.IMAGE_FOOTNOTE:
                image_footnote.extend(merge_para_with_text_v2(block))
        para_content = {
            'type': ContentTypeV2.IMAGE,
            'content': {
                'image_source': {'path': f"{img_buket_path}/{image_path}"},
                'image_caption': image_caption,
                'image_footnote': image_footnote,
            },
        }
    elif para_type == BlockType.TABLE:
        table_caption = []
        table_footnote = []
        image_path, html = _get_body_data(para_block)
        table_html = _format_embedded_html(html, img_buket_path)
        table_nest_level = 2 if table_html.count('<table') > 1 else 1
        if 'colspan' in table_html or 'rowspan' in table_html or table_nest_level > 1:
            table_type = ContentTypeV2.TABLE_COMPLEX
        else:
            table_type = ContentTypeV2.TABLE_SIMPLE
        for block in para_block.get('blocks', []):
            if block['type'] == BlockType.TABLE_CAPTION:
                table_caption.extend(merge_para_with_text_v2(block))
            if block['type'] == BlockType.TABLE_FOOTNOTE:
                table_footnote.extend(merge_para_with_text_v2(block))
        para_content = {
            'type': ContentTypeV2.TABLE,
            'content': {
                'image_source': {'path': f"{img_buket_path}/{image_path}"},
                'table_caption': table_caption,
                'table_footnote': table_footnote,
                'html': table_html,
                'table_type': table_type,
                'table_nest_level': table_nest_level,
            },
        }
    elif para_type == BlockType.CHART:
        chart_caption = []
        chart_footnote = []
        image_path, _ = _get_body_data(para_block)
        for block in para_block.get('blocks', []):
            if block['type'] == BlockType.CHART_CAPTION:
                chart_caption.extend(merge_para_with_text_v2(block))
            if block['type'] == BlockType.CHART_FOOTNOTE:
                chart_footnote.extend(merge_para_with_text_v2(block))
        para_content = {
            'type': ContentTypeV2.CHART,
            'content': {
                'image_source': {'path': f"{img_buket_path}/{image_path}"},
                'content': '',
                'chart_caption': chart_caption,
                'chart_footnote': chart_footnote,
            },
        }
    elif para_type == BlockType.CODE:
        code_caption = []
        code_footnote = []
        code_content = []
        for block in para_block.get('blocks', []):
            if block['type'] == BlockType.CODE_CAPTION:
                code_caption.extend(merge_para_with_text_v2(block))
            if block['type'] == BlockType.CODE_FOOTNOTE:
                code_footnote.extend(merge_para_with_text_v2(block))
            if block['type'] == BlockType.CODE_BODY:
                code_content = merge_para_with_text_v2(block)

        sub_type = para_block['sub_type']
        if sub_type == BlockType.CODE:
            para_content = {
                'type': ContentTypeV2.CODE,
                'content': {
                    'code_caption': code_caption,
                    'code_content': code_content,
                    'code_footnote': code_footnote,
                    'code_language': para_block.get('guess_lang', 'txt'),
                },
            }
        elif sub_type == BlockType.ALGORITHM:
            para_content = {
                'type': ContentTypeV2.ALGORITHM,
                'content': {
                    'algorithm_caption': code_caption,
                    'algorithm_content': code_content,
                    'algorithm_footnote': code_footnote,
                },
            }
        else:
            raise ValueError(f"Unknown code sub_type: {sub_type}")
    elif para_type == BlockType.REF_TEXT:
        list_items = []
        for block in _get_ref_text_item_blocks(para_block):
            item_content = merge_para_with_text_v2(block)
            if item_content:
                list_items.append({
                    'item_type': 'text',
                    'item_content': item_content,
                })
        para_content = {
            'type': ContentTypeV2.LIST,
            'content': {
                'list_type': ContentTypeV2.LIST_REF,
                'list_items': list_items,
            },
        }
    elif para_type == BlockType.LIST:
        list_items = []
        for block in _split_list_item_blocks(para_block):
            item_content = merge_para_with_text_v2(block)
            if item_content:
                list_items.append({
                    'item_type': 'text',
                    'item_content': item_content,
                })
        para_content = {
            'type': ContentTypeV2.LIST,
            'content': {
                'list_type': ContentTypeV2.LIST_TEXT,
                'attribute': para_block.get('attribute', 'unordered'),
                'list_items': list_items,
            },
        }
    elif para_type == BlockType.INDEX:
        list_items = []
        for block in _split_list_item_blocks(para_block):
            item_content = merge_para_with_text_v2(block)
            if item_content:
                list_items.append({
                    'item_type': 'text',
                    'item_content': item_content,
                })
        para_content = {
            'type': ContentTypeV2.INDEX,
            'content': {
                'list_type': ContentTypeV2.LIST_TEXT,
                'list_items': list_items,
            },
        }
    elif para_type == BlockType.SEAL:
        seal_span = _get_seal_span(para_block)
        if not seal_span:
            return None
        seal_text = _get_seal_text(para_block)
        para_content = {
            'type': ContentTypeV2.SEAL,
            'content': {
                'image_source': {
                    'path': f"{img_buket_path}/{seal_span.get('image_path', '')}",
                },
                'seal_content': (
                    [{'type': ContentTypeV2.SPAN_TEXT, 'content': seal_text}]
                    if seal_text else []
                ),
            },
        }

    if not para_content:
        return None

    bbox = _build_bbox(para_block.get('bbox'), page_size)
    if bbox:
        para_content['bbox'] = bbox

    return para_content