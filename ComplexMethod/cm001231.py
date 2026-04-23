async def test_store_agent_handler_get_missing_items(mocker):
    """Test StoreAgentHandler fetches approved agents without embeddings."""
    handler = StoreAgentHandler()

    mock_missing = [
        {
            "id": "agent-1",
            "name": "Test Agent",
            "description": "A test agent",
            "subHeading": "Test heading",
            "categories": ["AI", "Testing"],
        }
    ]

    with patch(
        "backend.api.features.store.content_handlers.query_raw_with_schema",
        return_value=mock_missing,
    ):
        items = await handler.get_missing_items(batch_size=10)

        assert len(items) == 1
        assert items[0].content_id == "agent-1"
        assert items[0].content_type == ContentType.STORE_AGENT
        assert "Test Agent" in items[0].searchable_text
        assert "A test agent" in items[0].searchable_text
        assert items[0].metadata["name"] == "Test Agent"
        assert items[0].user_id is None