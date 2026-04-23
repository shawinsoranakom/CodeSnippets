def union_make(pdf_info_dict: list,
               make_mode: str,
               img_buket_path: str = '',
               ):

    formula_enable = get_formula_enable(os.getenv('MINERU_VLM_FORMULA_ENABLE', 'True').lower() == 'true')
    table_enable = get_table_enable(os.getenv('MINERU_VLM_TABLE_ENABLE', 'True').lower() == 'true')

    output_content = []
    for page_info in pdf_info_dict:
        paras_of_layout = page_info.get('para_blocks')
        paras_of_discarded = page_info.get('discarded_blocks')
        page_idx = page_info.get('page_idx')
        page_size = page_info.get('page_size')
        if make_mode in [MakeMode.MM_MD, MakeMode.NLP_MD]:
            if not paras_of_layout:
                continue
            page_markdown = mk_blocks_to_markdown(paras_of_layout, make_mode, formula_enable, table_enable, img_buket_path)
            output_content.extend(page_markdown)
        elif make_mode == MakeMode.CONTENT_LIST:
            para_blocks = (paras_of_layout or []) + (paras_of_discarded or [])
            if not para_blocks:
                continue
            for para_block in para_blocks:
                para_content = make_blocks_to_content_list(para_block, img_buket_path, page_idx, page_size)
                output_content.append(para_content)
        elif make_mode == MakeMode.CONTENT_LIST_V2:
            # https://github.com/drunkpig/llm-webkit-mirror/blob/dev6/docs/specification/output_format/content_list_spec.md
            para_blocks = (paras_of_layout or []) + (paras_of_discarded or [])
            page_contents = []
            if para_blocks:
                for para_block in para_blocks:
                    para_content = make_blocks_to_content_list_v2(para_block, img_buket_path, page_size)
                    page_contents.append(para_content)
            output_content.append(page_contents)

    if make_mode in [MakeMode.MM_MD, MakeMode.NLP_MD]:
        return '\n\n'.join(output_content)
    elif make_mode in [MakeMode.CONTENT_LIST, MakeMode.CONTENT_LIST_V2]:
        return output_content
    return None