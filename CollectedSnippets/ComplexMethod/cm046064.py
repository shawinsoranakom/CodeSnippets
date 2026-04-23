def make_blocks_to_content_list_v2(para_block, img_buket_path):
    para_type = para_block['type']
    para_content = {}
    if para_type in [
        BlockType.HEADER,
        BlockType.FOOTER,
        BlockType.PAGE_FOOTNOTE,
    ]:
        if para_type == BlockType.HEADER:
            content_type = ContentTypeV2.PAGE_HEADER
        elif para_type == BlockType.FOOTER:
            content_type = ContentTypeV2.PAGE_FOOTER
        elif para_type == BlockType.PAGE_FOOTNOTE:
            content_type = ContentTypeV2.PAGE_FOOTNOTE
        else:
            raise ValueError(f"Unknown para_type: {para_type}")
        para_content = {
            'type': content_type,
            'content': {
                f"{content_type}_content": merge_para_with_text_v2(para_block),
            }
        }
    elif para_type == BlockType.TITLE:
        title_level = get_title_level(para_block)
        if title_level != 0:
            para_content = {
                'type': ContentTypeV2.TITLE,
                'content': {
                    "title_content": merge_para_with_text_v2(para_block),
                    "level": title_level
                }
            }
        else:
            para_content = {
                'type': ContentTypeV2.PARAGRAPH,
                'content': {
                    "paragraph_content": merge_para_with_text_v2(para_block),
                }
            }
    elif para_type in [
        BlockType.TEXT,
    ]:
        para_content = {
            'type': ContentTypeV2.PARAGRAPH,
            'content': {
                'paragraph_content': merge_para_with_text_v2(para_block),
            }
        }
    elif para_type == BlockType.INTERLINE_EQUATION:
        _, math_content = get_body_data(para_block)
        para_content = {
            'type': ContentTypeV2.EQUATION_INTERLINE,
            'content': {
                'math_content': math_content,
                'math_type': 'latex',
            }
        }
    elif para_type == BlockType.IMAGE:
        image_caption = []
        image_path, _ = get_body_data(para_block)
        image_source = {
            'path': f"{img_buket_path}/{image_path}",
        }
        for block in para_block['blocks']:
            if block['type'] == BlockType.IMAGE_CAPTION:
                image_caption.extend(merge_para_with_text_v2(block))
        para_content = {
            'type': ContentTypeV2.IMAGE,
            'content': {
                'image_source': image_source,
                'image_caption': image_caption,
            }
        }
    elif para_type == BlockType.TABLE:
        table_caption = []
        _, html = get_body_data(para_block)
        if html.count("<table") > 1:
            table_nest_level = 2
        else:
            table_nest_level = 1
        if (
                "colspan" in html or
                "rowspan" in html or
                table_nest_level > 1
        ):
            table_type = ContentTypeV2.TABLE_COMPLEX
        else:
            table_type = ContentTypeV2.TABLE_SIMPLE

        for block in para_block['blocks']:
            if block['type'] == BlockType.TABLE_CAPTION:
                table_caption.extend(merge_para_with_text_v2(block))
        para_content = {
            'type': ContentTypeV2.TABLE,
            'content': {
                'table_caption': table_caption,
                'html': _format_embedded_html(html, img_buket_path),
                'table_type': table_type,
                'table_nest_level': table_nest_level,
            }
        }
    elif para_type == BlockType.CHART:
        chart_caption = []
        image_path, chart_content = get_body_data(para_block)
        for block in para_block['blocks']:
            if block['type'] == BlockType.CHART_CAPTION:
                chart_caption.extend(merge_para_with_text_v2(block))
        para_content = {
            'type': ContentTypeV2.CHART,
            'content': {
                'image_source': {
                    'path': _build_media_path(img_buket_path, image_path),
                },
                'content': _format_embedded_html(chart_content, img_buket_path),
                'chart_caption': chart_caption,
            }
        }
    elif para_type == BlockType.LIST:
        list_type = ContentTypeV2.LIST_TEXT
        attribute = para_block.get('attribute', 'unordered')
        para_content = {
            'type': ContentTypeV2.LIST,
            'content': {
                'list_type': list_type,
                'attribute': attribute,
                'list_items': _flatten_list_items_v2(para_block),
            }
        }
    elif para_type == BlockType.INDEX:
        para_content = {
            'type': ContentTypeV2.INDEX,
            'content': {
                'list_type': ContentTypeV2.LIST_TEXT,
                'list_items': _flatten_list_items_v2(para_block),
            }
        }

    anchor = para_block.get("anchor")
    if isinstance(anchor, str) and anchor.strip():
        para_content["anchor"] = anchor.strip()

    return para_content