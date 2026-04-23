def plot_html_table(
    logi_points: Union[Union[np.ndarray, List]], cell_box_map: Dict[int, List[str]]
) -> str:
    # 初始化最大行数和列数
    max_row = 0
    max_col = 0
    # 计算最大行数和列数
    for point in logi_points:
        max_row = max(max_row, point[1] + 1)  # 加1是因为结束下标是包含在内的
        max_col = max(max_col, point[3] + 1)  # 加1是因为结束下标是包含在内的

    # 创建一个二维数组来存储 sorted_logi_points 中的元素
    grid = [[None] * max_col for _ in range(max_row)]

    valid_start_row = (1 << 16) - 1
    valid_start_col = (1 << 16) - 1
    valid_end_col = 0
    # 将 sorted_logi_points 中的元素填充到 grid 中
    for i, logic_point in enumerate(logi_points):
        row_start, row_end, col_start, col_end = (
            logic_point[0],
            logic_point[1],
            logic_point[2],
            logic_point[3],
        )
        ocr_rec_text_list = cell_box_map.get(i)
        if ocr_rec_text_list and "".join(ocr_rec_text_list):
            valid_start_row = min(row_start, valid_start_row)
            valid_start_col = min(col_start, valid_start_col)
            valid_end_col = max(col_end, valid_end_col)
        for row in range(row_start, row_end + 1):
            for col in range(col_start, col_end + 1):
                grid[row][col] = (i, row_start, row_end, col_start, col_end)

    # 创建表格
    table_html = "<html><body><table>"

    # 遍历每行
    for row in range(max_row):
        if row < valid_start_row:
            continue
        temp = "<tr>"
        # 遍历每一列
        for col in range(max_col):
            if col < valid_start_col or col > valid_end_col:
                continue
            if not grid[row][col]:
                temp += "<td></td>"
            else:
                i, row_start, row_end, col_start, col_end = grid[row][col]
                if not cell_box_map.get(i):
                    continue
                if row == row_start and col == col_start:
                    ocr_rec_text = cell_box_map.get(i)
                    # text = "<br>".join(ocr_rec_text)
                    text = "".join(ocr_rec_text)
                    # 如果是起始单元格
                    row_span = row_end - row_start + 1
                    col_span = col_end - col_start + 1
                    cell_content = (
                        f"<td rowspan={row_span} colspan={col_span}>{text}</td>"
                    )
                    temp += cell_content

        table_html = table_html + temp + "</tr>"

    table_html += "</table></body></html>"
    return table_html