def _get_unique_values(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        column: str,
        include_count: bool,
        sort_by_count: bool,
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
            return {"values": [], "counts": {}, "total_unique": 0}

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

        # Count values
        value_counts: dict[str, int] = {}
        for row in all_rows[1:]:  # Skip header
            value = str(row[col_idx]) if col_idx < len(row) else ""
            if value.strip():  # Skip empty values
                value_counts[value] = value_counts.get(value, 0) + 1

        # Sort values
        if sort_by_count:
            sorted_items = sorted(value_counts.items(), key=lambda x: -x[1])
            unique_values = [item[0] for item in sorted_items]
        else:
            unique_values = sorted(value_counts.keys())

        return {
            "values": unique_values,
            "counts": value_counts if include_count else {},
            "total_unique": len(unique_values),
        }