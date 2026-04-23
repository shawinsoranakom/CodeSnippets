def _manage_sheet(
        self,
        service,
        spreadsheet_id: str,
        operation: SheetOperation,
        sheet_name: str,
        source_sheet_id: int,
        destination_sheet_name: str,
    ) -> dict:
        requests = []

        if operation == SheetOperation.CREATE:
            # For CREATE, use sheet_name directly or default to "New Sheet"
            target_name = sheet_name or "New Sheet"
            requests.append({"addSheet": {"properties": {"title": target_name}}})
        elif operation == SheetOperation.DELETE:
            # For DELETE, resolve sheet name (fall back to first sheet if empty)
            target_name = resolve_sheet_name(
                service, spreadsheet_id, sheet_name or None
            )
            sid = sheet_id_by_name(service, spreadsheet_id, target_name)
            if sid is None:
                return {"error": f"Sheet '{target_name}' not found"}
            requests.append({"deleteSheet": {"sheetId": sid}})
        elif operation == SheetOperation.COPY:
            # For COPY, use source_sheet_id and destination_sheet_name directly
            requests.append(
                {
                    "duplicateSheet": {
                        "sourceSheetId": source_sheet_id,
                        "newSheetName": destination_sheet_name
                        or f"Copy of {source_sheet_id}",
                    }
                }
            )
        else:
            return {"error": f"Unknown operation: {operation}"}

        body = {"requests": requests}
        result = (
            service.spreadsheets()
            .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
            .execute()
        )
        return {"success": True, "result": result}