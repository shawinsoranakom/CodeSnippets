def mk_blocks_to_markdown(para_blocks, make_mode, img_buket_path='', page_idx=None):
    page_markdown = []
    for para_block in para_blocks:
        para_text = ''
        para_type = para_block['type']
        if para_type in [BlockType.TEXT, BlockType.INTERLINE_EQUATION]:
            para_text = merge_para_with_text(para_block)
            if para_type == BlockType.TEXT:
                bookmark_anchor = para_block.get("anchor")
                if (
                    isinstance(bookmark_anchor, str)
                    and bookmark_anchor.strip()
                    and bookmark_anchor.strip().startswith("_Toc")
                ):
                    para_text = f'<a id="{bookmark_anchor.strip()}"></a>\n{para_text}'
        elif para_type == BlockType.LIST:
            para_text = merge_list_to_markdown(para_block)
        elif para_type == BlockType.INDEX:
            para_text = merge_index_to_markdown(para_block)
        elif para_type == BlockType.TITLE:
            title_level = get_title_level(para_block)
            title_text = merge_para_with_text(para_block)
            bookmark_anchor = para_block.get("anchor")
            if isinstance(bookmark_anchor, str) and bookmark_anchor.strip():
                para_text = f'<a id="{bookmark_anchor.strip()}"></a>\n{"#" * title_level} {title_text}'
            else:
                para_text = f'{"#" * title_level} {title_text}'
        elif para_type == BlockType.IMAGE:
            if make_mode == MakeMode.NLP_MD:
                continue
            elif make_mode == MakeMode.MM_MD:
                for block in para_block['blocks']:  # 1st.拼image_body
                    if block['type'] == BlockType.IMAGE_BODY:
                        for line in block['lines']:
                            for span in line['spans']:
                                if span['type'] == ContentType.IMAGE:
                                    if span.get('image_path', ''):
                                        para_text += f"![]({img_buket_path}/{span['image_path']})"
                for block in para_block['blocks']:  # 2nd.拼image_caption
                    if block['type'] == BlockType.IMAGE_CAPTION:
                        para_text += '  \n' + merge_para_with_text(block)

        elif para_type == BlockType.TABLE:
            if make_mode == MakeMode.NLP_MD:
                continue
            elif make_mode == MakeMode.MM_MD:
                for block in para_block['blocks']:  # 1st.拼table_body
                    if block['type'] == BlockType.TABLE_BODY:
                        for line in block['lines']:
                            for span in line['spans']:
                                if span['type'] == ContentType.TABLE:
                                    para_text += f"\n{_format_embedded_html(span['html'], img_buket_path)}\n"
                for block in para_block['blocks']:  # 2nd.拼table_caption
                    if block['type'] == BlockType.TABLE_CAPTION:
                        para_text += '  \n' + merge_para_with_text(block)
        elif para_type == BlockType.CHART:
            if make_mode == MakeMode.NLP_MD:
                continue
            elif make_mode == MakeMode.MM_MD:
                image_path, chart_content = get_body_data(para_block)
                if chart_content:
                    para_text += f"\n{_format_embedded_html(chart_content, img_buket_path)}\n"
                elif image_path:
                    para_text += f"![]({_build_media_path(img_buket_path, image_path)})"
                else:
                    continue
                for block in para_block['blocks']:
                    if block['type'] == BlockType.CHART_CAPTION:
                        para_text += '  \n' + merge_para_with_text(block)
        if para_text.strip() == '':
            continue
        else:
            # page_markdown.append(para_text.strip())
            page_markdown.append(para_text.strip('\r\n'))

    return page_markdown