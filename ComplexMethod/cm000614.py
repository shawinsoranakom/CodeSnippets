def _filter_rows(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        filter_column: str,
        filter_value: str,
        operator: FilterOperator,
        match_case: bool,
        include_header: bool,
    ) -> dict:
        # Resolve sheet name
        target_sheet = resolve_sheet_name(service, spreadsheet_id, sheet_name or None)
        formatted_sheet = format_sheet_name(target_sheet)

        # Read all data from the sheet
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=formatted_sheet)
            .execute()
        )
        all_rows = result.get("values", [])

        if not all_rows:
            return {"rows": [], "row_indices": [], "count": 0}

        header = all_rows[0]
        data_rows = all_rows[1:]

        # Determine filter column index
        filter_col_idx = -1

        # First, try to match against header names (handles "ID", "No", "To", etc.)
        for idx, col_name in enumerate(header):
            if (match_case and col_name == filter_column) or (
                not match_case and col_name.lower() == filter_column.lower()
            ):
                filter_col_idx = idx
                break

        # If no header match and looks like a column letter (A, B, AA, etc.), try that
        if filter_col_idx < 0 and filter_column.isalpha() and len(filter_column) <= 2:
            filter_col_idx = _column_letter_to_index(filter_column)
            # Validate column letter is within data range
            if filter_col_idx >= len(header):
                raise ValueError(
                    f"Column '{filter_column}' (index {filter_col_idx}) is out of range. "
                    f"Sheet only has {len(header)} columns (A-{_index_to_column_letter(len(header) - 1)})."
                )

        if filter_col_idx < 0:
            raise ValueError(
                f"Column '{filter_column}' not found. Available columns: {header}"
            )

        # Filter rows
        filtered_rows = []
        row_indices = []

        for row_idx, row in enumerate(data_rows):
            # Get cell value (handle rows shorter than filter column)
            cell_value = row[filter_col_idx] if filter_col_idx < len(row) else ""

            if _apply_filter(str(cell_value), filter_value, operator, match_case):
                filtered_rows.append(row)
                row_indices.append(row_idx + 2)  # +2 for 1-based index and header

        # Prepare output
        output_rows = []
        if include_header:
            output_rows.append(header)
        output_rows.extend(filtered_rows)

        return {
            "rows": output_rows,
            "row_indices": row_indices,
            "count": len(filtered_rows),
        }