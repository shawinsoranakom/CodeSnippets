def _remove_duplicates(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        columns: list[str],
        keep: str,
        match_case: bool,
    ) -> dict:
        target_sheet = resolve_sheet_name(service, spreadsheet_id, sheet_name or None)
        formatted_sheet = format_sheet_name(target_sheet)
        sheet_id = sheet_id_by_name(service, spreadsheet_id, target_sheet)

        if sheet_id is None:
            raise ValueError(f"Sheet '{target_sheet}' not found")

        # Read all data
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=formatted_sheet)
            .execute()
        )
        all_rows = result.get("values", [])

        if len(all_rows) <= 1:  # Only header or empty
            return {
                "success": True,
                "removed_count": 0,
                "remaining_rows": len(all_rows),
            }

        header = all_rows[0]
        data_rows = all_rows[1:]

        # Determine which column indices to use for comparison
        # First try header name match, then column letter
        if columns:
            col_indices = []
            for col in columns:
                found = False
                # First try header name match
                for idx, col_name in enumerate(header):
                    if col_name.lower() == col.lower():
                        col_indices.append(idx)
                        found = True
                        break

                # If no header match and looks like a column letter, try that
                if not found and col.isalpha() and len(col) <= 2:
                    col_idx = _column_letter_to_index(col)
                    # Validate column letter is within data range
                    if col_idx >= len(header):
                        raise ValueError(
                            f"Column '{col}' (index {col_idx}) is out of range. "
                            f"Sheet only has {len(header)} columns (A-{_index_to_column_letter(len(header) - 1)})."
                        )
                    col_indices.append(col_idx)
                    found = True

                if not found:
                    raise ValueError(
                        f"Column '{col}' not found in sheet. "
                        f"Available columns: {', '.join(header)}"
                    )
        else:
            col_indices = list(range(len(header)))

        # Find duplicates
        seen: dict[tuple, int] = {}
        rows_to_delete: list[int] = []

        for row_idx, row in enumerate(data_rows):
            # Build key from specified columns
            key_parts = []
            for col_idx in col_indices:
                value = str(row[col_idx]) if col_idx < len(row) else ""
                if not match_case:
                    value = value.lower()
                key_parts.append(value)
            key = tuple(key_parts)

            if key in seen:
                if keep == "first":
                    # Delete this row (keep the first one we saw)
                    rows_to_delete.append(row_idx + 2)  # +2 for 1-based and header
                else:
                    # Delete the previous row, then update seen to keep this one
                    prev_row = seen[key]
                    rows_to_delete.append(prev_row)
                    seen[key] = row_idx + 2
            else:
                seen[key] = row_idx + 2

        if not rows_to_delete:
            return {
                "success": True,
                "removed_count": 0,
                "remaining_rows": len(all_rows),
            }

        # Sort in descending order to delete from bottom to top
        rows_to_delete = sorted(set(rows_to_delete), reverse=True)

        # Delete rows
        requests = []
        for row_idx in rows_to_delete:
            start_idx = row_idx - 1
            requests.append(
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": start_idx,
                            "endIndex": start_idx + 1,
                        }
                    }
                }
            )

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": requests}
        ).execute()

        remaining = len(all_rows) - len(rows_to_delete)
        return {
            "success": True,
            "removed_count": len(rows_to_delete),
            "remaining_rows": remaining,
        }