def _optimize_formula_number_blocks(pdf_info_list):
    for page_info in pdf_info_list:
        optimized_blocks = []
        blocks = page_info.get("preproc_blocks", [])
        for index, block in enumerate(blocks):
            if block.get("type") != BlockType.FORMULA_NUMBER:
                optimized_blocks.append(block)
                continue

            prev_block = blocks[index - 1] if index > 0 else None
            if prev_block and prev_block.get("type") == BlockType.INTERLINE_EQUATION:
                _append_formula_number_tag(prev_block, block)
                continue

            next_block = blocks[index + 1] if index + 1 < len(blocks) else None
            next_next_block = blocks[index + 2] if index + 2 < len(blocks) else None
            if (
                next_block
                and next_block.get("type") == BlockType.INTERLINE_EQUATION
                and (next_next_block is None or next_next_block.get("type") != BlockType.FORMULA_NUMBER)
            ):
                _append_formula_number_tag(next_block, block)
                continue

            block["type"] = BlockType.TEXT
            optimized_blocks.append(block)

        page_info["preproc_blocks"] = optimized_blocks