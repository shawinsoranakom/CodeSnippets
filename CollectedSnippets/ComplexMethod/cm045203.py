async def test_schema() -> None:
    """Test tool schema generation."""
    tool = AzureAISearchTool.create_full_text_search(
        name="test-search",
        endpoint=MOCK_ENDPOINT,
        index_name=MOCK_INDEX,
        credential=MOCK_CREDENTIAL,
    )

    schema = tool.schema
    assert schema["name"] == "test-search"
    assert "description" in schema
    assert "parameters" in schema
    assert "required" in schema["parameters"]
    assert schema["parameters"]["type"] == "object"
    assert "query" in schema["parameters"]["properties"]
    assert schema["parameters"]["required"] == ["query"]