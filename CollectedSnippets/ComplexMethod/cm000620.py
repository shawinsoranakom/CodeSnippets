def _get_row_count(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        include_header: bool,
        count_empty: bool,
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
            return {
                "total_rows": 0,
                "data_rows": 0,
                "last_row": 0,
                "column_count": 0,
            }

        # Count non-empty rows
        if count_empty:
            total_rows = len(all_rows)
            last_row = total_rows
        else:
            # Find last row with actual data
            last_row = 0
            for idx, row in enumerate(all_rows):
                if any(str(cell).strip() for cell in row):
                    last_row = idx + 1
            total_rows = last_row

        data_rows = total_rows - 1 if total_rows > 0 else 0
        if not include_header:
            total_rows = data_rows

        column_count = max(len(row) for row in all_rows) if all_rows else 0

        return {
            "total_rows": total_rows,
            "data_rows": data_rows,
            "last_row": last_row,
            "column_count": column_count,
        }