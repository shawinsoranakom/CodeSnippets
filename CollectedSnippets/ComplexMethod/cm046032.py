def make_blocks_to_markdown(paras_of_layout,
                                      mode,
                                      img_buket_path='',
                                      ):
    page_markdown = []
    for para_block in paras_of_layout:
        para_text = ''
        para_type = para_block['type']
        if para_type in [
            BlockType.TEXT,
            BlockType.LIST,
            BlockType.INDEX,
            BlockType.ABSTRACT,
            BlockType.REF_TEXT
        ]:
            para_text = merge_para_with_text(para_block)
        elif para_type == BlockType.TITLE:
            title_level = get_title_level(para_block)
            para_text = f'{"#" * title_level} {merge_para_with_text(para_block)}'
        elif para_type == BlockType.INTERLINE_EQUATION:
            if len(para_block['lines']) == 0 or len(para_block['lines'][0]['spans']) == 0:
                continue
            if para_block['lines'][0]['spans'][0].get('content', ''):
                para_text = merge_para_with_text(para_block)
            else:
                para_text = f"![]({img_buket_path}/{para_block['lines'][0]['spans'][0]['image_path']})"
        elif para_type == BlockType.SEAL:
            if len(para_block['lines']) == 0 or len(para_block['lines'][0]['spans']) == 0:
                continue
            para_text = f"![]({img_buket_path}/{para_block['lines'][0]['spans'][0]['image_path']})"
            if para_block['lines'][0]['spans'][0].get('content', []):
                content = " ".join(para_block['lines'][0]['spans'][0]['content'])
                para_text += f"  \n{content}"
        elif para_type == BlockType.IMAGE:
            if mode == MakeMode.NLP_MD:
                continue
            elif mode == MakeMode.MM_MD:
                para_text = merge_visual_blocks_to_markdown(para_block, img_buket_path)
        elif para_type == BlockType.CHART:
            if mode == MakeMode.NLP_MD:
                continue
            elif mode == MakeMode.MM_MD:
                para_text = merge_visual_blocks_to_markdown(para_block, img_buket_path)
        elif para_type == BlockType.TABLE:
            if mode == MakeMode.NLP_MD:
                continue
            elif mode == MakeMode.MM_MD:
                para_text = merge_visual_blocks_to_markdown(para_block, img_buket_path)
        elif para_type == BlockType.CODE:
            para_text = merge_visual_blocks_to_markdown(para_block)

        if para_text.strip() == '':
            continue
        else:
            page_markdown.append(para_text.strip())

    return page_markdown