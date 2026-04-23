def _apply_cell_merge(
    previous_state: TableMergeState,
    current_state: TableMergeState,
    header_count: int,
) -> None:
    """应用 cell_merge 语义合并。

    当 cell_merge 中的值为 1 时，将下表第一数据行对应单元格的内容
    追加到上表最后一行对应单元格中。全部为 1 时删除该数据行，
    混合时清空已合并单元格的内容但保留行。

    cell_merge 按视觉列索引对齐，通过构建视觉列映射来正确匹配
    两个表格中可能因 rowspan 而具有不同 <td> 元素数量的行。
    """
    cell_merge = current_state.owner_block.get("cell_merge")
    if not cell_merge:
        return

    rows2 = current_state.rows
    if header_count >= len(rows2):
        return
    if not previous_state.rows:
        return

    first_data_row = rows2[header_count]
    last_row = previous_state.rows[-1]

    cells1 = last_row.find_all(["td", "th"])
    cells2 = first_data_row.find_all(["td", "th"])

    # 构建视觉列到单元格索引的映射
    last_row_idx = len(previous_state.rows) - 1
    vcol_map1 = build_visual_col_mapping(previous_state.rows, last_row_idx)
    vcol_map2 = build_visual_col_mapping(rows2, header_count)

    # 构建视觉列 -> 单元格索引的反向映射（展开 colspan）
    vcol_to_cell1: dict[int, int] = {}
    for ci, start_vcol in enumerate(vcol_map1):
        colspan = int(cells1[ci].get("colspan", 1))
        for c in range(start_vcol, start_vcol + colspan):
            vcol_to_cell1[c] = ci
    vcol_to_cell2: dict[int, int] = {}
    for ci, start_vcol in enumerate(vcol_map2):
        colspan = int(cells2[ci].get("colspan", 1))
        for c in range(start_vcol, start_vcol + colspan):
            vcol_to_cell2[c] = ci

    # 按唯一 (src_cell_idx, dst_cell_idx) 对执行一次转移，避免 colspan 重复处理
    transferred_pairs: set[tuple[int, int]] = set()
    for vi, merge_flag in enumerate(cell_merge):
        if merge_flag == 1:
            ci1 = vcol_to_cell1.get(vi)
            ci2 = vcol_to_cell2.get(vi)
            if ci1 is not None and ci2 is not None:
                pair = (ci1, ci2)
                if pair not in transferred_pairs:
                    for child in list(cells2[ci2].children):
                        cells1[ci1].append(child.extract())
                    transferred_pairs.add(pair)

    # 只清空确实成功转移过的源单元格
    cleared_ci2: set[int] = set()
    for vi, merge_flag in enumerate(cell_merge):
        if merge_flag == 1:
            ci1 = vcol_to_cell1.get(vi)
            ci2 = vcol_to_cell2.get(vi)
            if ci1 is not None and ci2 is not None and ci2 not in cleared_ci2:
                cells2[ci2].clear()
                cleared_ci2.add(ci2)

    if not _row_has_semantic_content(first_data_row):
        _carry_rowspan_structure_to_next_row(rows2, header_count)
        first_data_row.extract()
        if first_data_row in rows2:
            rows2.remove(first_data_row)