def adjust_table_rows_colspan(
    rows,
    start_idx,
    end_idx,
    row_effective_cols,
    reference_structure,
    reference_visual_cols,
    target_cols,
    match_reference_row,
):
    """调整表格行的colspan属性以匹配目标列数."""
    reference_row_copy = deepcopy(match_reference_row)

    for row_idx in range(start_idx, end_idx):
        row = rows[row_idx]
        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        current_row_effective_cols = row_effective_cols[row_idx]
        current_row_cols = calculate_row_columns(row)

        if current_row_effective_cols >= target_cols or current_row_cols >= target_cols:
            continue

        if (
            calculate_visual_columns(row) == reference_visual_cols
            and check_row_columns_match(row, reference_row_copy)
        ):
            if len(cells) <= len(reference_structure):
                for cell_idx, cell in enumerate(cells):
                    if cell_idx < len(reference_structure) and reference_structure[cell_idx] > 1:
                        cell["colspan"] = str(reference_structure[cell_idx])
        else:
            cols_diff = target_cols - current_row_effective_cols
            if cols_diff > 0:
                last_cell = cells[-1]
                current_last_span = int(last_cell.get("colspan", 1))
                last_cell["colspan"] = str(current_last_span + cols_diff)