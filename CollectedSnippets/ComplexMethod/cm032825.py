def _parse_simple_headers(self, rows):
        if not rows:
            return [], 0
        header_row = rows[0]
        headers = []
        for cell in header_row:
            if cell.value is not None:
                header_value = str(cell.value).strip()
                if header_value:
                    headers.append(header_value)
            else:
                pass
        final_headers = []
        for i, cell in enumerate(header_row):
            if cell.value is not None:
                header_value = str(cell.value).strip()
                if header_value:
                    final_headers.append(header_value)
                else:
                    final_headers.append(f"Column_{i + 1}")
            else:
                final_headers.append(f"Column_{i + 1}")
        return final_headers, 1