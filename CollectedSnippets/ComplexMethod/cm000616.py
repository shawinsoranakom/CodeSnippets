def _get_column(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        column: str,
        include_header: bool,
        skip_empty: bool,
    ) -> dict:
        target_sheet = resolve_sheet_name(service, spreadsheet_id, sheet_name or None)
        formatted_sheet = format_sheet_name(target_sheet)

        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=formatted_sheet)
            .execute()
        )
        all_rows = result.get("values", [])

        if not all_rows:
            return {"values": [], "count": 0, "column_index": -1}

        header = all_rows[0]

        # Find column index - first try header name match, then column letter
        col_idx = -1
        for idx, col_name in enumerate(header):
            if col_name.lower() == column.lower():
                col_idx = idx
                break

        # If no header match and looks like a column letter, try that
        if col_idx < 0 and column.isalpha() and len(column) <= 2:
            col_idx = _column_letter_to_index(column)
            # Validate column letter is within data range
            if col_idx >= len(header):
                raise ValueError(
                    f"Column '{column}' (index {col_idx}) is out of range. "
                    f"Sheet only has {len(header)} columns (A-{_index_to_column_letter(len(header) - 1)})."
                )

        if col_idx < 0:
            raise ValueError(
                f"Column '{column}' not found. Available columns: {header}"
            )

        # Extract column values
        values = []
        start_row = 0 if include_header else 1

        for row in all_rows[start_row:]:
            value = row[col_idx] if col_idx < len(row) else ""
            if skip_empty and not str(value).strip():
                continue
            values.append(str(value))

        return {"values": values, "count": len(values), "column_index": col_idx}