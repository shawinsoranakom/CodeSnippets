async def test_create_and_update_field():
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

    field_name = f"test_field_{postfix}"
    field_type = TableFieldType.SINGLE_LINE_TEXT
    field = await create_field(credentials, base_id, table_id, field_type, field_name)
    assert field.get("name") == field_name

    field_id = field.get("id")

    assert field_id is not None
    assert isinstance(field_id, str)

    field_name = f"test_field_updated_{postfix}"
    field = await update_field(credentials, base_id, table_id, field_id, field_name)
    assert field.get("name") == field_name

    field_description = "test_description_updated"
    field = await update_field(
        credentials, base_id, table_id, field_id, description=field_description
    )
    assert field.get("description") == field_description