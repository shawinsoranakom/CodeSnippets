def _sync_para_titles_to_preproc(page_info_list):
    for page_info in page_info_list:
        para_title_map = {}
        for block in page_info.get("para_blocks", []):
            if block.get("type") in TITLE_BLOCK_TYPES:
                para_title_map[_get_title_block_identity(block)] = block

        if len(para_title_map) == 0:
            continue

        for block in page_info.get("preproc_blocks", []):
            if block.get("type") not in TITLE_BLOCK_TYPES:
                continue

            para_block = para_title_map.get(_get_title_block_identity(block))
            if para_block is None:
                continue

            block["type"] = para_block.get("type", block.get("type"))
            if "level" in para_block:
                block["level"] = para_block["level"]