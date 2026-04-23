def _parse_table(self, table_lines):
        """解析表格内容为结构化数据"""
        try:
            headers = self._normalize_table_row(table_lines[0])

            separator_index = next(
                (i for i, line in enumerate(table_lines) if self._is_separator_row(line)),
                1
            )

            data_rows = []
            for line in table_lines[separator_index + 1:]:
                cells = self._normalize_table_row(line)
                # 确保单元格数量与表头一致
                while len(cells) < len(headers):
                    cells.append('')
                cells = cells[:len(headers)]
                data_rows.append(cells)

            if headers and data_rows:
                return {
                    'headers': headers,
                    'data': data_rows
                }
        except Exception as e:
            print(f"解析表格时发生错误: {str(e)}")

        return None