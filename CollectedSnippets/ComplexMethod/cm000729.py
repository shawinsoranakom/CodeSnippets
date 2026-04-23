async def create_record(
    credentials: Credentials,
    base_id: str,
    table_id_or_name: str,
    fields: dict[str, Any] | None = None,
    records: list[dict[str, Any]] | None = None,
    return_fields_by_field_id: bool | None = None,
    typecast: bool | None = None,
) -> dict[str, dict[str, dict[str, str]]]:
    assert fields or records, "At least one of fields or records must be provided"
    assert not (fields and records), "Only one of fields or records can be provided"
    if records is not None:
        assert (
            len(records) <= 10
        ), "Only up to 10 records can be provided when using records"

    params: dict[str, str | bool | dict[str, Any] | list[dict[str, Any]]] = {}
    if fields:
        params["fields"] = fields
    if records:
        params["records"] = records
    if return_fields_by_field_id:
        params["returnFieldsByFieldId"] = return_fields_by_field_id
    if typecast:
        params["typecast"] = typecast

    response = await Requests().post(
        f"https://api.airtable.com/v0/{base_id}/{table_id_or_name}",
        headers={"Authorization": credentials.auth_header()},
        json=_convert_bools(params),
    )

    return response.json()