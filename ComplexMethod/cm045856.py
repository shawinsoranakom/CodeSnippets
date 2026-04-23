def has_content(r, c):
            """检查指定单元格（0-based索引）是否有内容（有值或属于合并区域）。"""
            if r < 0 or c < 0 or r > max_row or c > max_col:
                return False

            # 1. 检查单元格直接值
            cell = sheet.cell(row=r + 1, column=c + 1)
            if cell.value is not None:
                return True

            # 2. 检查是否属于某个合并单元格区域
            for mr in sheet.merged_cells.ranges:
                if cell.coordinate in mr:
                    return True
            return False