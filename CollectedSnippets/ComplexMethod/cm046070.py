def _scan_row_visual_sources(rows, target_row_index: int) -> tuple[dict[int, tuple[int, int]], int]:
    """扫描到目标行，记录每个视觉列当前由哪个源单元格占据。"""
    if target_row_index < 0:
        target_row_index += len(rows)
    if target_row_index < 0 or target_row_index >= len(rows):
        return {}, 0

    # occupied[row_idx][col_idx] = (source_row_idx, source_cell_idx)
    occupied: dict[int, dict[int, tuple[int, int]]] = {}
    total_cols = 0

    for r_idx in range(target_row_index + 1):
        occupied_row = occupied.setdefault(r_idx, {})
        col_idx = 0
        cells = rows[r_idx].find_all(["td", "th"])
        for cell_idx, cell in enumerate(cells):
            while col_idx in occupied_row:
                col_idx += 1
            colspan = int(cell.get("colspan", 1))
            rowspan = int(cell.get("rowspan", 1))
            source_marker = (r_idx, cell_idx)
            for ro in range(rowspan):
                target_idx = r_idx + ro
                occ = occupied.setdefault(target_idx, {})
                for c in range(col_idx, col_idx + colspan):
                    occ[c] = source_marker
            col_idx += colspan
            total_cols = max(total_cols, col_idx)

    return occupied.get(target_row_index, {}), total_cols