def merge_table(page_info_list):
    """合并跨页表格."""
    state_cache: dict[int, TableMergeState] = {}
    merged_away_blocks: set[int] = set()

    for page_idx in range(len(page_info_list) - 1, -1, -1):
        if page_idx == 0:
            continue

        page_info = page_info_list[page_idx]
        previous_page_info = page_info_list[page_idx - 1]

        if not (page_info["para_blocks"] and page_info["para_blocks"][0]["type"] == BlockType.TABLE):
            continue

        if not (
            previous_page_info["para_blocks"]
            and previous_page_info["para_blocks"][-1]["type"] == BlockType.TABLE
        ):
            continue

        current_table_block = page_info["para_blocks"][0]
        previous_table_block = previous_page_info["para_blocks"][-1]

        current_state = _get_or_create_table_state(current_table_block, state_cache)
        previous_state = _get_or_create_table_state(previous_table_block, state_cache)
        if current_state is None or previous_state is None:
            continue

        wait_merge_table_footnotes = [
            block for block in current_table_block["blocks"] if block["type"] == BlockType.TABLE_FOOTNOTE
        ]

        if not can_merge_tables(current_state, previous_state):
            continue

        perform_table_merge(
            previous_state,
            current_state,
            previous_table_block,
            wait_merge_table_footnotes,
        )

        merged_away_blocks.add(id(current_table_block))
        for block in current_table_block["blocks"]:
            block["lines"] = []
            block[SplitFlag.LINES_DELETED] = True

    for state in state_cache.values():
        if state.dirty and id(state.owner_block) not in merged_away_blocks:
            _serialize_table_state_html(state)