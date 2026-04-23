def _format_cells(
        self,
        service,
        spreadsheet_id: str,
        a1_range: str,
        background_color: dict,
        text_color: dict,
        bold: bool,
        italic: bool,
        font_size: int,
    ) -> dict:
        sheet_name, cell_range = parse_a1_notation(a1_range)
        sheet_name = resolve_sheet_name(service, spreadsheet_id, sheet_name)

        sheet_id = sheet_id_by_name(service, spreadsheet_id, sheet_name)
        if sheet_id is None:
            return {"error": f"Sheet '{sheet_name}' not found"}

        try:
            start_cell, end_cell = cell_range.split(":")
            start_col = ord(start_cell[0].upper()) - ord("A")
            start_row = int(start_cell[1:]) - 1
            end_col = ord(end_cell[0].upper()) - ord("A") + 1
            end_row = int(end_cell[1:])
        except (ValueError, IndexError):
            return {"error": f"Invalid range format: {a1_range}"}

        cell_format: dict = {"userEnteredFormat": {}}
        if background_color:
            cell_format["userEnteredFormat"]["backgroundColor"] = background_color

        text_format: dict = {}
        if text_color:
            text_format["foregroundColor"] = text_color
        if bold:
            text_format["bold"] = True
        if italic:
            text_format["italic"] = True
        if font_size != 10:
            text_format["fontSize"] = font_size
        if text_format:
            cell_format["userEnteredFormat"]["textFormat"] = text_format

        body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": start_row,
                            "endRowIndex": end_row,
                            "startColumnIndex": start_col,
                            "endColumnIndex": end_col,
                        },
                        "cell": cell_format,
                        "fields": "userEnteredFormat(backgroundColor,textFormat)",
                    }
                }
            ]
        }

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body
        ).execute()
        return {"success": True}