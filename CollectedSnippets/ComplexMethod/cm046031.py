def para_split(page_info_list):
    all_blocks = []
    for page_info in page_info_list:
        blocks = copy.deepcopy(page_info['preproc_blocks'])
        for block in blocks:
            block['page_num'] = page_info['page_idx']
            block['page_size'] = page_info['page_size']
        all_blocks.extend(blocks)

    __para_merge_page(all_blocks)
    for page_info in page_info_list:
        page_info['para_blocks'] = []
        for block in all_blocks:
            if 'page_num' in block:
                if block['page_num'] == page_info['page_idx']:
                    if block['type'] == BlockType.VERTICAL_TEXT:
                        block['type'] = BlockType.TEXT
                    page_info['para_blocks'].append(block)
                    # 从block中删除不需要的page_num和page_size字段
                    del block['page_num']
                    del block['page_size']