async def list_records(
    credentials: Credentials,
    base_id: str,
    table_id_or_name: str,
    # Query parameters
    time_zone: AirtableTimeZones | None = None,
    user_local: str | None = None,
    page_size: int | None = None,
    max_records: int | None = None,
    offset: str | None = None,
    view: str | None = None,
    sort: list[dict[str, str]] | None = None,
    filter_by_formula: str | None = None,
    cell_format: dict[str, str] | None = None,
    fields: list[str] | None = None,
    return_fields_by_field_id: bool | None = None,
    record_metadata: list[str] | None = None,
) -> dict[str, list[dict[str, dict[str, str]]]]:

    params: dict[str, str | dict[str, str] | list[dict[str, str]] | list[str]] = {}
    if time_zone:
        params["timeZone"] = time_zone
    if user_local:
        params["userLocal"] = user_local
    if page_size:
        params["pageSize"] = str(page_size)
    if max_records:
        params["maxRecords"] = str(max_records)
    if offset:
        params["offset"] = offset
    if view:
        params["view"] = view
    if sort:
        params["sort"] = sort
    if filter_by_formula:
        params["filterByFormula"] = filter_by_formula
    if cell_format:
        params["cellFormat"] = cell_format
    if fields:
        params["fields"] = fields
    if return_fields_by_field_id:
        params["returnFieldsByFieldId"] = str(return_fields_by_field_id)
    if record_metadata:
        params["recordMetadata"] = record_metadata

    response = await Requests().get(
        f"https://api.airtable.com/v0/{base_id}/{table_id_or_name}",
        headers={"Authorization": credentials.auth_header()},
        json=_convert_bools(params),
    )
    return response.json()