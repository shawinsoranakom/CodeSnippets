async def test_webhook_management():
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
    webhook_specification = WebhookSpecification(
        filters=WebhookFilters(
            dataTypes=["tableData", "tableFields", "tableMetadata"],
            changeTypes=["add", "update", "remove"],
        )
    )
    response = await create_webhook(credentials, base_id, webhook_specification)
    assert response is not None, f"Checking create webhook response: {response}"
    assert (
        response.get("id") is not None
    ), f"Checking create webhook response id: {response}"
    assert (
        response.get("macSecretBase64") is not None
    ), f"Checking create webhook response macSecretBase64: {response}"

    webhook_id = response.get("id")
    assert webhook_id is not None, f"Webhook ID: {webhook_id}"
    assert isinstance(webhook_id, str)

    response = await create_record(
        credentials, base_id, table_id, fields={"test_field": "test_value"}
    )
    assert response is not None, f"Checking create record response: {response}"
    assert (
        response.get("id") is not None
    ), f"Checking create record response id: {response}"
    fields = response.get("fields")
    assert fields is not None, f"Checking create record response fields: {response}"
    assert (
        fields.get("test_field") == "test_value"
    ), f"Checking create record response fields test_field: {response}"

    response = await list_webhook_payloads(credentials, base_id, webhook_id)
    assert response is not None, f"Checking list webhook payloads response: {response}"

    response = await delete_webhook(credentials, base_id, webhook_id)