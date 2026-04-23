def _build_hierarchical_headers(self, ws, rows, header_rows):
        headers = []
        max_col = max(len(row) for row in rows[:header_rows]) if header_rows > 0 else 0
        merged_ranges = list(ws.merged_cells.ranges)
        for col_idx in range(max_col):
            header_parts = []
            for row_idx in range(header_rows):
                if col_idx < len(rows[row_idx]):
                    cell_value = rows[row_idx][col_idx].value
                    merged_value = self._get_merged_cell_value(ws, row_idx + 1, col_idx + 1, merged_ranges)
                    if merged_value is not None:
                        cell_value = merged_value
                    if cell_value is not None:
                        cell_value = str(cell_value).strip()
                        if cell_value and cell_value not in header_parts and self._is_valid_header_part(cell_value):
                            header_parts.append(cell_value)
            if header_parts:
                header = "-".join(header_parts)
                headers.append(header)
            else:
                headers.append(f"Column_{col_idx + 1}")
        final_headers = [h for h in headers if h and h != "-"]
        return final_headers