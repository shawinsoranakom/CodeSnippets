def _search_range(
        self,
        service,
        spreadsheet_id: str,
        range_name: str,
        sheet_name: str,
        find_text: str,
        match_case: bool,
        match_entire_cell: bool,
        find_all: bool,
        locations: list,
    ):
        """Search within a specific range and add results to locations list."""
        values_result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        values = values_result.get("values", [])

        # Parse range to get starting position
        _, cell_range = parse_a1_notation(range_name)
        start_col = 0
        start_row = 0

        if cell_range and ":" in cell_range:
            start_cell = cell_range.split(":")[0]
            # Parse A1 notation (e.g., "B3" -> col=1, row=2)
            col_part = ""
            row_part = ""
            for char in start_cell:
                if char.isalpha():
                    col_part += char
                elif char.isdigit():
                    row_part += char

            if col_part:
                start_col = ord(col_part.upper()) - ord("A")
            if row_part:
                start_row = int(row_part) - 1

        # Search through values
        for row_idx, row in enumerate(values):
            for col_idx, cell_value in enumerate(row):
                if cell_value is None:
                    continue

                cell_str = str(cell_value)

                # Apply search criteria
                search_text = find_text if match_case else find_text.lower()
                cell_text = cell_str if match_case else cell_str.lower()

                found = False
                if match_entire_cell:
                    found = cell_text == search_text
                else:
                    found = search_text in cell_text

                if found:
                    # Calculate actual spreadsheet position
                    actual_row = start_row + row_idx + 1
                    actual_col = start_col + col_idx + 1
                    col_letter = chr(ord("A") + start_col + col_idx)
                    address = f"{col_letter}{actual_row}"

                    location = {
                        "sheet": sheet_name,
                        "row": actual_row,
                        "column": actual_col,
                        "address": address,
                        "value": cell_str,
                    }
                    locations.append(location)

                    # Stop after first match if find_all is False
                    if not find_all:
                        return