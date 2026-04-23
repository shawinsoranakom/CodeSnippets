def perform_table_merge(
    previous_state: TableMergeState,
    current_state: TableMergeState,
    previous_table_block,
    wait_merge_table_footnotes,
):
    """执行表格合并操作."""
    header_count, _, _ = detect_table_headers(previous_state, current_state)

    rows1 = previous_state.rows
    rows2 = current_state.rows

    previous_adjusted = False

    if rows1 and rows2 and header_count < len(rows2):
        last_row1 = rows1[-1]
        first_data_row2 = rows2[header_count]
        table_cols1 = previous_state.total_cols
        table_cols2 = current_state.total_cols

        if table_cols1 > table_cols2:
            reference_structure = [
                int(cell.get("colspan", 1)) for cell in last_row1.find_all(["td", "th"])
            ]
            reference_visual_cols = calculate_visual_columns(last_row1)
            adjust_table_rows_colspan(
                rows2,
                header_count,
                len(rows2),
                current_state.row_effective_cols,
                reference_structure,
                reference_visual_cols,
                table_cols1,
                first_data_row2,
            )
        elif table_cols2 > table_cols1:
            reference_structure = [
                int(cell.get("colspan", 1)) for cell in first_data_row2.find_all(["td", "th"])
            ]
            reference_visual_cols = calculate_visual_columns(first_data_row2)
            adjust_table_rows_colspan(
                rows1,
                0,
                len(rows1),
                previous_state.row_effective_cols,
                reference_structure,
                reference_visual_cols,
                table_cols2,
                last_row1,
            )
            previous_adjusted = True

    if previous_adjusted:
        _refresh_table_state_metrics(previous_state)

    _apply_cell_merge(previous_state, current_state, header_count)

    appended_rows = rows2[header_count:]
    append_start_idx = len(previous_state.rows)
    merged_rows = []

    if previous_state.tbody and current_state.tbody:
        for row in appended_rows:
            row.extract()
            previous_state.tbody.append(row)
            merged_rows.append(row)

    previous_state.rows.extend(merged_rows)

    if merged_rows:
        appended_scan = _scan_rows(
            merged_rows,
            initial_occupied=previous_state.tail_occupied,
            start_row_idx=append_start_idx,
        )
        previous_state.row_effective_cols.extend(appended_scan.row_effective_cols)
        previous_state.total_cols = max(previous_state.total_cols, appended_scan.total_cols)
        if appended_scan.last_nonempty_row_metrics is not None:
            previous_state.last_data_row_metrics = appended_scan.last_nonempty_row_metrics
        previous_state.tail_occupied = appended_scan.tail_occupied

    previous_table_block["blocks"] = [
        block for block in previous_table_block["blocks"] if block["type"] != BlockType.TABLE_FOOTNOTE
    ]
    for table_footnote in wait_merge_table_footnotes:
        temp_table_footnote = table_footnote.copy()
        temp_table_footnote[SplitFlag.CROSS_PAGE] = True
        previous_table_block["blocks"].append(temp_table_footnote)

    previous_state.dirty = True