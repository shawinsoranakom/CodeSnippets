def _append_to_sheet(call: ServiceCall, entry: GoogleSheetsConfigEntry) -> None:
    """Run append in the executor."""
    client = Client(Credentials(entry.data[CONF_TOKEN][CONF_ACCESS_TOKEN]))  # type: ignore[no-untyped-call]
    try:
        sheet = client.open_by_key(entry.unique_id)
    except RefreshError:
        entry.async_start_reauth(call.hass)
        raise
    except APIError as ex:
        raise HomeAssistantError("Failed to write data") from ex

    worksheet = sheet.worksheet(call.data.get(WORKSHEET, sheet.sheet1.title))
    columns: list[str] = next(iter(worksheet.get_values("A1:ZZ1")), [])
    add_created_column = call.data[ADD_CREATED_COLUMN]
    now = str(datetime.now())
    rows = []
    for d in call.data[DATA]:
        row_data = ({"created": now} | d) if add_created_column else d
        row = [row_data.get(column, "") for column in columns]
        for key, value in row_data.items():
            if key not in columns:
                columns.append(key)
                worksheet.update_cell(1, len(columns), key)
                row.append(value)
        rows.append(row)
    worksheet.append_rows(rows, value_input_option=ValueInputOption.user_entered)