def _delete_column(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        column: str,
    ) -> dict:
        target_sheet = resolve_sheet_name(service, spreadsheet_id, sheet_name or None)
        formatted_sheet = format_sheet_name(target_sheet)
        sheet_id = sheet_id_by_name(service, spreadsheet_id, target_sheet)

        if sheet_id is None:
            raise ValueError(f"Sheet '{target_sheet}' not found")

        # Get header to find column by name or validate column letter
        header_result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=f"{formatted_sheet}!1:1")
            .execute()
        )
        header = (
            header_result.get("values", [[]])[0] if header_result.get("values") else []
        )

        # Find column index - first try header name match, then column letter
        col_idx = -1
        for idx, h in enumerate(header):
            if h.lower() == column.lower():
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
            raise ValueError(f"Column '{column}' not found")

        # Delete the column
        request = {
            "deleteDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": col_idx,
                    "endIndex": col_idx + 1,
                }
            }
        }

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": [request]}
        ).execute()

        return {"success": True}