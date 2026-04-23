def _add_column(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        header: str,
        position: str,
        default_value: str,
    ) -> dict:
        target_sheet = resolve_sheet_name(service, spreadsheet_id, sheet_name or None)
        formatted_sheet = format_sheet_name(target_sheet)
        sheet_id = sheet_id_by_name(service, spreadsheet_id, target_sheet)

        if sheet_id is None:
            raise ValueError(f"Sheet '{target_sheet}' not found")

        # Get current data to determine column count and row count
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=formatted_sheet)
            .execute()
        )
        all_rows = result.get("values", [])
        current_col_count = max(len(row) for row in all_rows) if all_rows else 0
        row_count = len(all_rows)

        # Determine target column index
        if position.lower() == "end":
            col_idx = current_col_count
        elif position.isalpha() and len(position) <= 2:
            col_idx = _column_letter_to_index(position)
            # Insert a new column at this position
            insert_request = {
                "insertDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": col_idx,
                        "endIndex": col_idx + 1,
                    },
                    "inheritFromBefore": col_idx > 0,
                }
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body={"requests": [insert_request]}
            ).execute()
        else:
            raise ValueError(
                f"Invalid position: '{position}'. Use 'end' or a column letter."
            )

        col_letter = _index_to_column_letter(col_idx)

        # Write header
        header_range = f"{formatted_sheet}!{col_letter}1"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=header_range,
            valueInputOption="USER_ENTERED",
            body={"values": [[header]]},
        ).execute()

        # Fill default value if provided and there are data rows
        if default_value and row_count > 1:
            values_to_fill = [[default_value]] * (row_count - 1)
            data_range = f"{formatted_sheet}!{col_letter}2:{col_letter}{row_count}"
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=data_range,
                valueInputOption="USER_ENTERED",
                body={"values": values_to_fill},
            ).execute()

        return {
            "success": True,
            "column_letter": col_letter,
            "column_index": col_idx,
        }