def __para_merge_page(blocks):
    page_text_blocks_groups = __process_blocks(blocks)
    for text_blocks_group in page_text_blocks_groups:
        if len(text_blocks_group) > 0:
            # 需要先在合并前对所有block判断是否为list or index block
            for block in text_blocks_group:
                block_type = __is_list_or_index_block(block)
                block['type'] = block_type
                # logger.info(f"{block['type']}:{block}")

        if len(text_blocks_group) > 1:
            # 在合并前判断这个group 是否是一个 list group
            is_list_group = __is_list_group(text_blocks_group)

            # 倒序遍历
            for i in range(len(text_blocks_group) - 1, -1, -1):
                current_block = text_blocks_group[i]

                # 检查是否有前一个块
                if i - 1 >= 0:
                    prev_block = text_blocks_group[i - 1]

                    if (
                        current_block['type'] == BlockType.VERTICAL_TEXT
                        and prev_block['type'] == BlockType.VERTICAL_TEXT
                    ):
                        __merge_2_vertical_text_blocks(current_block, prev_block)
                    elif (
                        current_block['type'] == BlockType.TEXT
                        and prev_block['type'] == BlockType.TEXT
                        and not is_list_group
                    ):
                        __merge_2_text_blocks(current_block, prev_block)
                    elif (
                        current_block['type'] == BlockType.LIST
                        and prev_block['type'] == BlockType.LIST
                    ) or (
                        current_block['type'] == BlockType.INDEX
                        and prev_block['type'] == BlockType.INDEX
                    ):
                        __merge_2_list_blocks(current_block, prev_block)

        else:
            continue