def _protect_range(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        range_str: str,
        description: str,
        warning_only: bool,
    ) -> dict:
        target_sheet = resolve_sheet_name(service, spreadsheet_id, sheet_name or None)
        sheet_id = sheet_id_by_name(service, spreadsheet_id, target_sheet)

        if sheet_id is None:
            raise ValueError(f"Sheet '{target_sheet}' not found")

        protected_range: dict = {"sheetId": sheet_id}

        if range_str:
            # Parse specific range
            if "!" in range_str:
                range_str = range_str.split("!")[1]

            match = re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", range_str.upper())
            if not match:
                raise ValueError(f"Invalid range format: {range_str}")

            protected_range["startRowIndex"] = int(match.group(2)) - 1
            protected_range["endRowIndex"] = int(match.group(4))
            protected_range["startColumnIndex"] = _column_letter_to_index(
                match.group(1)
            )
            protected_range["endColumnIndex"] = (
                _column_letter_to_index(match.group(3)) + 1
            )

        request = {
            "addProtectedRange": {
                "protectedRange": {
                    "range": protected_range,
                    "description": description,
                    "warningOnly": warning_only,
                }
            }
        }

        result = (
            service.spreadsheets()
            .batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": [request]})
            .execute()
        )

        protection_id = 0
        replies = result.get("replies", [])
        if replies and "addProtectedRange" in replies[0]:
            protection_id = replies[0]["addProtectedRange"]["protectedRange"][
                "protectedRangeId"
            ]

        return {"success": True, "protection_id": protection_id}