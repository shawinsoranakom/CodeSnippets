def can_merge_tables(current_state: TableMergeState, previous_state: TableMergeState):
    """判断两个表格是否可以合并."""
    current_table_block = current_state.owner_block
    previous_table_block = previous_state.owner_block

    if "blocks" not in previous_table_block or "blocks" not in current_table_block:
        raise ValueError(
            "can_merge_tables() requires owner_block with 'blocks' key. "
            "For HTML-only states from build_table_state_from_html(), use can_merge_by_structure() instead."
        )

    footnote_count = sum(
        1 for block in previous_table_block["blocks"] if block["type"] == BlockType.TABLE_FOOTNOTE
    )
    caption_blocks = [
        block for block in current_table_block["blocks"] if block["type"] == BlockType.TABLE_CAPTION
    ]
    if caption_blocks:
        has_continuation_marker = False
        for block in caption_blocks:
            caption_text = full_to_half(merge_para_with_text(block).strip()).lower()
            if (
                any(caption_text.endswith(marker.lower()) for marker in CONTINUATION_END_MARKERS)
                or any(marker.lower() in caption_text for marker in CONTINUATION_INLINE_MARKERS)
            ):
                has_continuation_marker = True
                break

        if not has_continuation_marker:
            return False

        if footnote_count > 1:
            return False
    elif footnote_count > 0:
        return False

    x0_t1, _, x1_t1, _ = current_table_block["bbox"]
    x0_t2, _, x1_t2, _ = previous_table_block["bbox"]
    table1_width = x1_t1 - x0_t1
    table2_width = x1_t2 - x0_t2

    if abs(table1_width - table2_width) / min(table1_width, table2_width) >= 0.1:
        return False

    if previous_state.total_cols == current_state.total_cols:
        return True

    return check_rows_match(previous_state, current_state)