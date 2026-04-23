def _extract_tables_from_text(self, text):
        """从文本中提取所有表格内容"""
        if not isinstance(text, str):
            return []

        tables = []
        current_table = []
        is_in_table = False

        for line in text.split('\n'):
            line = line.strip()
            if not line:
                if is_in_table and current_table:
                    if len(current_table) >= 2:
                        tables.append(current_table)
                    current_table = []
                    is_in_table = False
                continue

            if '|' in line:
                if not is_in_table:
                    is_in_table = True
                current_table.append(line)
            else:
                if is_in_table and current_table:
                    if len(current_table) >= 2:
                        tables.append(current_table)
                    current_table = []
                    is_in_table = False

        if is_in_table and current_table and len(current_table) >= 2:
            tables.append(current_table)

        return tables