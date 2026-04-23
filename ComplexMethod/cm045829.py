def decode_logic_points(self, pred_structures):
        logic_points = []
        current_row = 0
        current_col = 0
        max_rows = 0
        max_cols = 0
        occupied_cells = {}  # 用于记录已经被占用的单元格

        def is_occupied(row, col):
            return (row, col) in occupied_cells

        def mark_occupied(row, col, rowspan, colspan):
            for r in range(row, row + rowspan):
                for c in range(col, col + colspan):
                    occupied_cells[(r, c)] = True

        i = 0
        while i < len(pred_structures):
            token = pred_structures[i]

            if token == "<tr>":
                current_col = 0  # 每次遇到 <tr> 时，重置当前列号
            elif token == "</tr>":
                current_row += 1  # 行结束，行号增加
            elif token.startswith("<td"):
                colspan = 1
                rowspan = 1
                j = i
                if token != "<td></td>":
                    j += 1
                    # 提取 colspan 和 rowspan 属性
                    while j < len(pred_structures) and not pred_structures[
                        j
                    ].startswith(">"):
                        if "colspan=" in pred_structures[j]:
                            colspan = int(pred_structures[j].split("=")[1].strip("\"'"))
                        elif "rowspan=" in pred_structures[j]:
                            rowspan = int(pred_structures[j].split("=")[1].strip("\"'"))
                        j += 1

                # 跳过已经处理过的属性 token
                i = j

                # 找到下一个未被占用的列
                while is_occupied(current_row, current_col):
                    current_col += 1

                # 计算逻辑坐标
                r_start = current_row
                r_end = current_row + rowspan - 1
                col_start = current_col
                col_end = current_col + colspan - 1

                # 记录逻辑坐标
                logic_points.append([r_start, r_end, col_start, col_end])

                # 标记占用的单元格
                mark_occupied(r_start, col_start, rowspan, colspan)

                # 更新当前列号
                current_col += colspan

                # 更新最大行数和列数
                max_rows = max(max_rows, r_end + 1)
                max_cols = max(max_cols, col_end + 1)

            i += 1

        return logic_points