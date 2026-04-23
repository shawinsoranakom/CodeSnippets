def create_document(self, history):
        """
        处理聊天历史中的所有表格并创建Excel文档

        Args:
            history: 聊天历史列表

        Returns:
            Workbook: 处理完成的Excel工作簿对象，如果没有表格则返回None
        """
        has_tables = False

        # 删除默认创建的工作表
        default_sheet = self.workbook['Sheet']
        self.workbook.remove(default_sheet)

        # 遍历所有回答
        for i in range(1, len(history), 2):
            answer = history[i]
            tables = self._extract_tables_from_text(answer)

            for table_lines in tables:
                parsed_table = self._parse_table(table_lines)
                if parsed_table:
                    self._table_count += 1
                    sheet = self._create_sheet(i // 2 + 1, self._table_count)

                    # 写入表头
                    for col, header in enumerate(parsed_table['headers'], 1):
                        sheet.cell(row=1, column=col, value=header)

                    # 写入数据
                    for row_idx, row_data in enumerate(parsed_table['data'], 2):
                        for col_idx, value in enumerate(row_data, 1):
                            sheet.cell(row=row_idx, column=col_idx, value=value)

                    has_tables = True

        return self.workbook if has_tables else None