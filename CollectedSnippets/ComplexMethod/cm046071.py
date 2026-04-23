def detect_table_headers(state1: TableMergeState, state2: TableMergeState, max_header_rows: int = MAX_HEADER_ROWS):
    """检测并比较两个表格的表头，仅扫描前几行."""
    front_rows1 = state1.front_header_info[:max_header_rows]
    front_rows2 = state2.front_header_info[:max_header_rows]

    min_rows = min(len(front_rows1), len(front_rows2), max_header_rows)
    header_rows = 0
    headers_match = True
    header_texts = []

    for row_idx in range(min_rows):
        row1 = front_rows1[row_idx]
        row2 = front_rows2[row_idx]
        structure_match = (
            row1.cell_count == row2.cell_count
            and row1.effective_cols == row2.effective_cols
            and row1.colspans == row2.colspans
            and row1.rowspans == row2.rowspans
            and row1.normalized_texts == row2.normalized_texts
        )

        if structure_match:
            header_rows += 1
            header_texts.append(list(row1.display_texts))
        else:
            headers_match = header_rows > 0
            break

    if header_rows == 0:
        header_rows, headers_match, header_texts = _detect_table_headers_visual(
            state1, state2, max_header_rows=max_header_rows
        )

    return header_rows, headers_match, header_texts