def _parse_markdown_table_lines(self, table_lines: list):
        """
        Parse a list of Markdown table lines into a pandas DataFrame.

        Args:
            table_lines: List of strings, each representing a row in the Markdown table
                        (excluding separator lines like |---|---|)

        Returns:
            pandas DataFrame with the table data, or None if parsing fails
        """
        import pandas as pd

        if not table_lines:
            return None

        rows = []
        headers = None

        def _coerce_excel_cell_type(cell: str):
            # Convert markdown cell text to native numeric types when safe,so Excel writes numeric cells instead of text.
            if not isinstance(cell, str):
                return cell

            value = cell.strip()
            if value == "":
                return ""

            # Keep values like "00123" as text to avoid losing leading zeros.
            if re.match(r"^[+-]?0\d+$", value):
                return cell

            # Support thousand separators like 1,234 or 1,234.56
            numeric_candidate = value
            if re.match(r"^[+-]?\d{1,3}(,\d{3})+(\.\d+)?$", value):
                numeric_candidate = value.replace(",", "")

            if re.match(r"^[+-]?\d+$", numeric_candidate):
                try:
                    return int(numeric_candidate)
                except ValueError:
                    return cell

            if re.match(r"^[+-]?(\d+\.\d+|\d+\.|\.\d+)([eE][+-]?\d+)?$", numeric_candidate) or re.match(r"^[+-]?\d+[eE][+-]?\d+$", numeric_candidate):
                try:
                    return float(numeric_candidate)
                except ValueError:
                    return cell

            return cell

        for line in table_lines:
            # Split by | and clean up
            cells = [cell.strip() for cell in line.split('|')]
            # Remove empty first and last elements from split (caused by leading/trailing |)
            cells = [c for c in cells if c]

            if headers is None:
                headers = cells
            else:
                cells = [_coerce_excel_cell_type(c) for c in cells]
                rows.append(cells)

        if headers and rows:
            # Ensure all rows have same number of columns as headers
            normalized_rows = []
            for row in rows:
                while len(row) < len(headers):
                    row.append('')
                normalized_rows.append(row[:len(headers)])

            return pd.DataFrame(normalized_rows, columns=headers)

        return None