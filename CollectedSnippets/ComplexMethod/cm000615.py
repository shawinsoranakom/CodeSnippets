def _lookup_row(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        lookup_column: str,
        lookup_value: str,
        return_columns: list[str],
        match_case: bool,
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
            return {"row": [], "row_dict": {}, "row_index": 0, "found": False}

        header = all_rows[0]
        data_rows = all_rows[1:]

        # Find lookup column index - first try header name match, then column letter
        lookup_col_idx = -1
        for idx, col_name in enumerate(header):
            if (match_case and col_name == lookup_column) or (
                not match_case and col_name.lower() == lookup_column.lower()
            ):
                lookup_col_idx = idx
                break

        # If no header match and looks like a column letter, try that
        if lookup_col_idx < 0 and lookup_column.isalpha() and len(lookup_column) <= 2:
            lookup_col_idx = _column_letter_to_index(lookup_column)
            # Validate column letter is within data range
            if lookup_col_idx >= len(header):
                raise ValueError(
                    f"Column '{lookup_column}' (index {lookup_col_idx}) is out of range. "
                    f"Sheet only has {len(header)} columns (A-{_index_to_column_letter(len(header) - 1)})."
                )

        if lookup_col_idx < 0:
            raise ValueError(
                f"Lookup column '{lookup_column}' not found. Available: {header}"
            )

        # Find return column indices - first try header name match, then column letter
        return_col_indices = []
        return_col_headers = []
        if return_columns:
            for ret_col in return_columns:
                found = False
                # First try header name match
                for idx, col_name in enumerate(header):
                    if (match_case and col_name == ret_col) or (
                        not match_case and col_name.lower() == ret_col.lower()
                    ):
                        return_col_indices.append(idx)
                        return_col_headers.append(col_name)
                        found = True
                        break

                # If no header match and looks like a column letter, try that
                if not found and ret_col.isalpha() and len(ret_col) <= 2:
                    idx = _column_letter_to_index(ret_col)
                    # Validate column letter is within data range
                    if idx >= len(header):
                        raise ValueError(
                            f"Return column '{ret_col}' (index {idx}) is out of range. "
                            f"Sheet only has {len(header)} columns (A-{_index_to_column_letter(len(header) - 1)})."
                        )
                    return_col_indices.append(idx)
                    return_col_headers.append(header[idx])
                    found = True

                if not found:
                    raise ValueError(
                        f"Return column '{ret_col}' not found. Available: {header}"
                    )
        else:
            return_col_indices = list(range(len(header)))
            return_col_headers = header

        # Search for matching row
        compare_value = lookup_value if match_case else lookup_value.lower()

        for row_idx, row in enumerate(data_rows):
            cell_value = row[lookup_col_idx] if lookup_col_idx < len(row) else ""
            compare_cell = str(cell_value) if match_case else str(cell_value).lower()

            if compare_cell == compare_value:
                # Found a match - extract requested columns
                result_row = []
                result_dict = {}
                for i, col_idx in enumerate(return_col_indices):
                    value = row[col_idx] if col_idx < len(row) else ""
                    result_row.append(value)
                    result_dict[return_col_headers[i]] = value

                return {
                    "row": result_row,
                    "row_dict": result_dict,
                    "row_index": row_idx + 2,
                    "found": True,
                }

        return {"row": [], "row_dict": {}, "row_index": 0, "found": False}