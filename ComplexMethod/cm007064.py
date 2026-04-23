def _create_dataframe(self, rows: list[list[str]], *, has_header: bool) -> pd.DataFrame:
        """Create DataFrame from parsed rows."""
        if has_header and len(rows) > 1:
            header = rows[0]
            data_rows = rows[1:]
            header_col_count = len(header)

            # Validate that all data rows have the same number of columns as header
            for i, row in enumerate(data_rows):
                row_col_count = len(row)
                if row_col_count != header_col_count:
                    msg = (
                        f"Header mismatch: {header_col_count} column(s) in header vs "
                        f"{row_col_count} column(s) in data row {i + 1}. "
                        "Please ensure the header has the same number of columns as your data."
                    )
                    raise ValueError(msg)

            return pd.DataFrame(data_rows, columns=header)

        max_cols = max(len(row) for row in rows) if rows else 0
        columns = [f"col_{i}" for i in range(max_cols)]
        return pd.DataFrame(rows, columns=columns)