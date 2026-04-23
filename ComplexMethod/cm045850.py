def _find_true_data_bounds(self, sheet: Worksheet) -> DataRegion:
        """查找工作表中真实的数据边界（最小/最大行列）。

        该函数扫描所有单元格，找到包含所有非空单元格或合并单元格区域的
        最小矩形范围，返回边界的行列索引。

        参数：
            sheet: 待分析的工作表。

        返回：
            覆盖所有数据和合并单元格的最小矩形区域 DataRegion。
            若工作表为空，则默认返回 (1, 1, 1, 1)。
        """
        min_row, min_col = None, None
        max_row, max_col = 0, 0

        # 遍历所有有值的单元格，动态更新边界
        for cell in sheet._cells.values():
            if cell.value is not None:
                r, c = cell.row, cell.column
                min_row = r if min_row is None else min(min_row, r)
                min_col = c if min_col is None else min(min_col, c)
                max_row = max(max_row, r)
                max_col = max(max_col, c)

        # 将合并单元格的范围也纳入边界计算
        for merged in sheet.merged_cells.ranges:
            min_row = (
                merged.min_row if min_row is None else min(min_row, merged.min_row)
            )
            min_col = (
                merged.min_col if min_col is None else min(min_col, merged.min_col)
            )
            max_row = max(max_row, merged.max_row)
            max_col = max(max_col, merged.max_col)

        # 若工作表中没有任何数据，默认返回 (1, 1, 1, 1)
        if min_row is None or min_col is None:
            min_row = min_col = max_row = max_col = 1

        return DataRegion(min_row, max_row, min_col, max_col)