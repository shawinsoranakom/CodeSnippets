async def test_create_update_table():

    key = getenv("AIRTABLE_API_KEY")
    if not key:
        return pytest.skip("AIRTABLE_API_KEY is not set")

    credentials = APIKeyCredentials(
        provider="airtable",
        api_key=SecretStr(key),
    )
    postfix = uuid4().hex[:4]
    workspace_id = "wsphuHmfllg7V3Brd"
    response = await create_base(credentials, workspace_id, "API Testing Base")
    assert response is not None, f"Checking create base response: {response}"
    assert (
        response.get("id") is not None
    ), f"Checking create base response id: {response}"
    base_id = response.get("id")
    assert base_id is not None, f"Checking create base response id: {base_id}"

    response = await list_bases(credentials)
    assert response is not None, f"Checking list bases response: {response}"
    assert "API Testing Base" in [
        base.get("name") for base in response.get("bases", [])
    ], f"Checking list bases response bases: {response}"

    table_name = f"test_table_{postfix}"
    table_fields = [{"name": "test_field", "type": "singleLineText"}]
    table = await create_table(credentials, base_id, table_name, table_fields)
    assert table.get("name") == table_name

    table_id = table.get("id")

    assert table_id is not None

    table_name = f"test_table_updated_{postfix}"
    table_description = "test_description_updated"
    table = await update_table(
        credentials,
        base_id,
        table_id,
        table_name=table_name,
        table_description=table_description,
    )
    assert table.get("name") == table_name
    assert table.get("description") == table_description