def _find_text(
        self,
        service,
        spreadsheet_id: str,
        find_text: str,
        sheet_id: int,
        match_case: bool,
        match_entire_cell: bool,
        find_all: bool,
        range: str,
    ) -> dict:
        # Unfortunately, Google Sheets API doesn't have a dedicated "find-only" operation
        # that returns cell locations. The findReplace operation only returns a count.
        # So we need to search through the values manually to get location details.

        locations = []
        search_range = range if range else None

        if not search_range:
            # If no range specified, search entire spreadsheet
            meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheets = meta.get("sheets", [])

            # Filter to specific sheet if provided
            if sheet_id >= 0:
                sheets = [
                    s
                    for s in sheets
                    if s.get("properties", {}).get("sheetId") == sheet_id
                ]

            # Search each sheet
            for sheet in sheets:
                sheet_name = sheet.get("properties", {}).get("title", "")
                sheet_range = f"'{sheet_name}'"
                self._search_range(
                    service,
                    spreadsheet_id,
                    sheet_range,
                    sheet_name,
                    find_text,
                    match_case,
                    match_entire_cell,
                    find_all,
                    locations,
                )
                if not find_all and locations:
                    break
        else:
            # Search specific range
            sheet_name, cell_range = parse_a1_notation(search_range)
            if not sheet_name:
                # Get first sheet name if not specified
                meta = (
                    service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                )
                sheet_name = (
                    meta.get("sheets", [{}])[0]
                    .get("properties", {})
                    .get("title", "Sheet1")
                )
                search_range = f"'{sheet_name}'!{search_range}"

            self._search_range(
                service,
                spreadsheet_id,
                search_range,
                sheet_name,
                find_text,
                match_case,
                match_entire_cell,
                find_all,
                locations,
            )

        return {"locations": locations, "count": len(locations)}