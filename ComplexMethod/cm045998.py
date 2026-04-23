def mk_blocks_to_markdown(para_blocks, make_mode, formula_enable, table_enable, img_buket_path=''):
    page_markdown = []
    for para_block in para_blocks:
        para_text = ''
        para_type = para_block['type']
        if para_type in [BlockType.TEXT, BlockType.INTERLINE_EQUATION, BlockType.PHONETIC, BlockType.REF_TEXT]:
            para_text = merge_para_with_text(para_block, formula_enable=formula_enable, img_buket_path=img_buket_path)
        elif para_type == BlockType.LIST:
            for block in para_block['blocks']:
                item_text = merge_para_with_text(
                    block,
                    formula_enable=formula_enable,
                    img_buket_path=img_buket_path,
                    escape_text_block_prefix=False,
                )
                para_text += f"{item_text}  \n"
        elif para_type == BlockType.TITLE:
            title_level = get_title_level(para_block)
            para_text = f'{"#" * title_level} {merge_para_with_text(para_block)}'
        elif para_type == BlockType.IMAGE:
            if make_mode == MakeMode.NLP_MD:
                continue
            elif make_mode == MakeMode.MM_MD:
                para_text = _merge_visual_blocks_to_markdown(
                    para_block,
                    img_buket_path,
                    table_enable=table_enable,
                )

        elif para_type == BlockType.TABLE:
            if make_mode == MakeMode.NLP_MD:
                continue
            elif make_mode == MakeMode.MM_MD:
                para_text = _merge_visual_blocks_to_markdown(
                    para_block,
                    img_buket_path,
                    table_enable=table_enable,
                )
        elif para_type == BlockType.CHART:
            if make_mode == MakeMode.NLP_MD:
                continue
            elif make_mode == MakeMode.MM_MD:
                para_text = _merge_visual_blocks_to_markdown(
                    para_block,
                    img_buket_path,
                    table_enable=table_enable,
                )
        elif para_type == BlockType.CODE:
            para_text = _merge_visual_blocks_to_markdown(
                para_block,
                img_buket_path,
                table_enable=table_enable,
            )

        if para_text.strip() == '':
            continue
        else:
            # page_markdown.append(para_text.strip() + '  ')
            page_markdown.append(para_text.strip())

    return page_markdown