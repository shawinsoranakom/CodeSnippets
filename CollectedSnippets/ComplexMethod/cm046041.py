def merge_para_text_blocks(pdf_info_list, allow_cross_page=False):
    ordered_blocks = []
    for page_info in pdf_info_list:
        page_idx = page_info.get("page_idx")
        for order_idx, block in enumerate(page_info.get("para_blocks", [])):
            ordered_blocks.append((page_idx, order_idx, block))

    for current_index in range(len(ordered_blocks) - 1, -1, -1):
        current_page_idx, _, current_block = ordered_blocks[current_index]
        if current_block.get("type") != BlockType.TEXT:
            continue
        if not current_block.get("merge_prev"):
            continue
        if not _block_has_lines(current_block):
            continue

        previous_block = _find_previous_text_block(
            ordered_blocks,
            current_index,
            current_block,
            current_page_idx,
            allow_cross_page=allow_cross_page,
        )
        if previous_block is None:
            continue

        previous_page_idx, _, previous_text_block = previous_block
        _merge_text_block(
            current_block,
            previous_text_block,
            is_cross_page=current_page_idx != previous_page_idx,
        )