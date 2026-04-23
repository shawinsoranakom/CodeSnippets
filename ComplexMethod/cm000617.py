def _sort_sheet(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        sort_column: str,
        sort_order: SortOrder,
        secondary_column: str,
        secondary_order: SortOrder,
        has_header: bool,
    ) -> dict:
        target_sheet = resolve_sheet_name(service, spreadsheet_id, sheet_name or None)
        sheet_id = sheet_id_by_name(service, spreadsheet_id, target_sheet)

        if sheet_id is None:
            raise ValueError(f"Sheet '{target_sheet}' not found")

        # Get sheet metadata to find column indices and grid properties
        meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_meta = None
        for sheet in meta.get("sheets", []):
            if sheet.get("properties", {}).get("sheetId") == sheet_id:
                sheet_meta = sheet
                break

        if not sheet_meta:
            raise ValueError(f"Could not find metadata for sheet '{target_sheet}'")

        grid_props = sheet_meta.get("properties", {}).get("gridProperties", {})
        row_count = grid_props.get("rowCount", 1000)
        col_count = grid_props.get("columnCount", 26)

        # Get header to resolve column names
        formatted_sheet = format_sheet_name(target_sheet)
        header_result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=f"{formatted_sheet}!1:1")
            .execute()
        )
        header = (
            header_result.get("values", [[]])[0] if header_result.get("values") else []
        )

        # Find primary sort column index - first try header name match, then column letter
        sort_col_idx = -1
        for idx, col_name in enumerate(header):
            if col_name.lower() == sort_column.lower():
                sort_col_idx = idx
                break

        # If no header match and looks like a column letter, try that
        if sort_col_idx < 0 and sort_column.isalpha() and len(sort_column) <= 2:
            sort_col_idx = _column_letter_to_index(sort_column)
            # Validate column letter is within data range
            if sort_col_idx >= len(header):
                raise ValueError(
                    f"Sort column '{sort_column}' (index {sort_col_idx}) is out of range. "
                    f"Sheet only has {len(header)} columns (A-{_index_to_column_letter(len(header) - 1)})."
                )

        if sort_col_idx < 0:
            raise ValueError(
                f"Sort column '{sort_column}' not found. Available: {header}"
            )

        # Build sort specs
        sort_specs = [
            {
                "dimensionIndex": sort_col_idx,
                "sortOrder": (
                    "ASCENDING" if sort_order == SortOrder.ASCENDING else "DESCENDING"
                ),
            }
        ]

        # Add secondary sort if specified
        if secondary_column:
            sec_col_idx = -1
            # First try header name match
            for idx, col_name in enumerate(header):
                if col_name.lower() == secondary_column.lower():
                    sec_col_idx = idx
                    break

            # If no header match and looks like a column letter, try that
            if (
                sec_col_idx < 0
                and secondary_column.isalpha()
                and len(secondary_column) <= 2
            ):
                sec_col_idx = _column_letter_to_index(secondary_column)
                # Validate column letter is within data range
                if sec_col_idx >= len(header):
                    raise ValueError(
                        f"Secondary sort column '{secondary_column}' (index {sec_col_idx}) is out of range. "
                        f"Sheet only has {len(header)} columns (A-{_index_to_column_letter(len(header) - 1)})."
                    )

            if sec_col_idx < 0:
                raise ValueError(
                    f"Secondary sort column '{secondary_column}' not found. Available: {header}"
                )

            sort_specs.append(
                {
                    "dimensionIndex": sec_col_idx,
                    "sortOrder": (
                        "ASCENDING"
                        if secondary_order == SortOrder.ASCENDING
                        else "DESCENDING"
                    ),
                }
            )

        # Build sort range request
        start_row = 1 if has_header else 0  # Skip header if present

        request = {
            "sortRange": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": start_row,
                    "endRowIndex": row_count,
                    "startColumnIndex": 0,
                    "endColumnIndex": col_count,
                },
                "sortSpecs": sort_specs,
            }
        }

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body={"requests": [request]}
        ).execute()

        return {"success": True}