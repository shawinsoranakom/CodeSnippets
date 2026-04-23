def _update_row(
        self,
        service,
        spreadsheet_id: str,
        sheet_name: str,
        row_index: int,
        values: list[str],
        dict_values: dict[str, str],
    ) -> dict:
        target_sheet = resolve_sheet_name(service, spreadsheet_id, sheet_name or None)
        formatted_sheet = format_sheet_name(target_sheet)

        if dict_values:
            # Get header to map column names to indices
            header_result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=f"{formatted_sheet}!1:1")
                .execute()
            )
            header = (
                header_result.get("values", [[]])[0]
                if header_result.get("values")
                else []
            )

            # Get current row values
            row_range = f"{formatted_sheet}!{row_index}:{row_index}"
            current_result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=row_range)
                .execute()
            )
            current_row = (
                current_result.get("values", [[]])[0]
                if current_result.get("values")
                else []
            )

            # Extend current row to match header length
            while len(current_row) < len(header):
                current_row.append("")

            # Update specific columns from dict - validate all column names first
            for col_name in dict_values.keys():
                found = False
                for h in header:
                    if h.lower() == col_name.lower():
                        found = True
                        break
                if not found:
                    raise ValueError(
                        f"Column '{col_name}' not found in sheet. "
                        f"Available columns: {', '.join(header)}"
                    )

            # Now apply updates
            updated_count = 0
            for col_name, value in dict_values.items():
                for idx, h in enumerate(header):
                    if h.lower() == col_name.lower():
                        current_row[idx] = value
                        updated_count += 1
                        break

            values = current_row
        else:
            updated_count = len(values)

        # Write the row
        write_range = f"{formatted_sheet}!A{row_index}"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=write_range,
            valueInputOption="USER_ENTERED",
            body={"values": [values]},
        ).execute()

        return {"success": True, "updatedCells": updated_count}