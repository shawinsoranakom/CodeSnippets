async def test_record_management():
    key = getenv("AIRTABLE_API_KEY")
    if not key:
        return pytest.skip("AIRTABLE_API_KEY is not set")

    credentials = APIKeyCredentials(
        provider="airtable",
        api_key=SecretStr(key),
    )
    postfix = uuid4().hex[:4]
    base_id = "appZPxegHEU3kDc1S"
    table_name = f"test_table_{postfix}"
    table_fields = [{"name": "test_field", "type": "singleLineText"}]
    table = await create_table(credentials, base_id, table_name, table_fields)
    assert table.get("name") == table_name

    table_id = table.get("id")
    assert table_id is not None

    # Create a record
    record_fields = {"test_field": "test_value"}
    record = await create_record(credentials, base_id, table_id, fields=record_fields)
    fields = record.get("fields")
    assert fields is not None
    assert isinstance(fields, dict)
    assert fields.get("test_field") == "test_value"

    record_id = record.get("id")

    assert record_id is not None
    assert isinstance(record_id, str)

    # Get a record
    record = await get_record(credentials, base_id, table_id, record_id)
    fields = record.get("fields")
    assert fields is not None
    assert isinstance(fields, dict)
    assert fields.get("test_field") == "test_value"

    # Updata a record
    record_fields = {"test_field": "test_value_updated"}
    record = await update_record(
        credentials, base_id, table_id, record_id, fields=record_fields
    )
    fields = record.get("fields")
    assert fields is not None
    assert isinstance(fields, dict)
    assert fields.get("test_field") == "test_value_updated"

    # Delete a record
    record = await delete_record(credentials, base_id, table_id, record_id)
    assert record is not None
    assert record.get("id") == record_id
    assert record.get("deleted")

    # Create 2 records
    records = [
        {"fields": {"test_field": "test_value_1"}},
        {"fields": {"test_field": "test_value_2"}},
    ]
    response = await create_record(credentials, base_id, table_id, records=records)
    created_records = response.get("records")
    assert created_records is not None
    assert isinstance(created_records, list)
    assert len(created_records) == 2, f"Created records: {created_records}"
    first_record = created_records[0]  # type: ignore
    second_record = created_records[1]  # type: ignore
    first_record_id = first_record.get("id")
    second_record_id = second_record.get("id")
    assert first_record_id is not None
    assert second_record_id is not None
    assert first_record_id != second_record_id
    first_fields = first_record.get("fields")
    second_fields = second_record.get("fields")
    assert first_fields is not None
    assert second_fields is not None
    assert first_fields.get("test_field") == "test_value_1"  # type: ignore
    assert second_fields.get("test_field") == "test_value_2"  # type: ignore

    # List records
    response = await list_records(credentials, base_id, table_id)
    records = response.get("records")
    assert records is not None
    assert len(records) == 2, f"Records: {records}"
    assert isinstance(records, list), f"Type of records: {type(records)}"

    # Update multiple records
    records = [
        {"id": first_record_id, "fields": {"test_field": "test_value_1_updated"}},
        {"id": second_record_id, "fields": {"test_field": "test_value_2_updated"}},
    ]
    response = await update_multiple_records(
        credentials, base_id, table_id, records=records
    )
    updated_records = response.get("records")
    assert updated_records is not None
    assert len(updated_records) == 2, f"Updated records: {updated_records}"
    assert isinstance(
        updated_records, list
    ), f"Type of updated records: {type(updated_records)}"
    first_updated = updated_records[0]  # type: ignore
    second_updated = updated_records[1]  # type: ignore
    first_updated_fields = first_updated.get("fields")
    second_updated_fields = second_updated.get("fields")
    assert first_updated_fields is not None
    assert second_updated_fields is not None
    assert first_updated_fields.get("test_field") == "test_value_1_updated"  # type: ignore
    assert second_updated_fields.get("test_field") == "test_value_2_updated"  # type: ignore

    # Delete multiple records
    assert isinstance(first_record_id, str)
    assert isinstance(second_record_id, str)
    response = await delete_multiple_records(
        credentials, base_id, table_id, records=[first_record_id, second_record_id]
    )
    deleted_records = response.get("records")
    assert deleted_records is not None
    assert len(deleted_records) == 2, f"Deleted records: {deleted_records}"
    assert isinstance(
        deleted_records, list
    ), f"Type of deleted records: {type(deleted_records)}"
    first_deleted = deleted_records[0]  # type: ignore
    second_deleted = deleted_records[1]  # type: ignore
    assert first_deleted.get("deleted")
    assert second_deleted.get("deleted")