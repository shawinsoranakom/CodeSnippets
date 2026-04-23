def _find_data_bounds(ws, image_map, max_rows=None):
    """Return (min_row, max_row, min_col, max_col) 1-based, or None if the sheet is empty."""
    min_r = min_c = float("inf")
    max_r = max_c = 0

    # Non-empty cells
    for cell in ws._cells.values():
        if cell.value is not None:
            r, c = cell.row, cell.column
            if max_rows is not None and r > max_rows:
                continue
            min_r = min(min_r, r)
            max_r = max(max_r, r)
            min_c = min(min_c, c)
            max_c = max(max_c, c)

    # Merged cell ranges
    for mr in ws.merged_cells.ranges:
        r1, r2 = mr.min_row, mr.max_row
        if max_rows is not None:
            r2 = min(r2, max_rows)
        if r1 > r2:
            continue
        min_r = min(min_r, r1)
        max_r = max(max_r, r2)
        min_c = min(min_c, mr.min_col)
        max_c = max(max_c, mr.max_col)

    # Image anchors (0-based -> 1-based)
    for img_r0, img_c0 in image_map:
        r, c = img_r0 + 1, img_c0 + 1
        if max_rows is not None and r > max_rows:
            continue
        min_r = min(min_r, r)
        max_r = max(max_r, r)
        min_c = min(min_c, c)
        max_c = max(max_c, c)

    if max_r == 0:
        return None
    return (int(min_r), int(max_r), int(min_c), int(max_c))