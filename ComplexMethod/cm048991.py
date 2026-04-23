def extract_spreadsheet(content):
            sheets_csv = []
            tables = content.xpath('.//table:table', namespaces=main_namespaces)
            for table in tables:
                table_rows = []
                table_name = table.get(f'{{{main_namespaces["table"]}}}name')
                if not table_name:
                    table_name = f"Sheet{len(sheets_csv) + 1}"
                table_name_escaped = _csv_escape(table_name)
                for row in table.xpath('.//table:table-row', namespaces=main_namespaces):
                    row_repeat = row.get(f'{{{main_namespaces["table"]}}}number-rows-repeated')
                    row_repeat_count = min(int(row_repeat), MAX_ROW_REPEAT) if row_repeat and row_repeat.isdigit() else 1

                    cells = extract_row(row)
                    if not any(cells):
                        continue

                    while cells and not cells[-1]:
                        cells.pop()

                    row_str = ','.join([table_name_escaped] + list(map(_csv_escape, cells)))
                    if row_str.replace(',', '').strip():
                        table_rows.extend([row_str] * row_repeat_count)

                if table_rows:
                    sheets_csv.append('\n'.join(table_rows))

            return sheets_csv