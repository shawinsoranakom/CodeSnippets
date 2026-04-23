async def test_store_agent_handler_real_db():
    """Test StoreAgentHandler with real database queries."""
    handler = StoreAgentHandler()

    # Get stats from real DB
    stats = await handler.get_stats()

    # Stats should have correct structure
    assert "total" in stats
    assert "with_embeddings" in stats
    assert "without_embeddings" in stats
    assert stats["total"] >= 0
    assert stats["with_embeddings"] >= 0
    assert stats["without_embeddings"] >= 0

    # Get missing items (max 1 to keep test fast)
    items = await handler.get_missing_items(batch_size=1)

    # Items should be list (may be empty if all have embeddings)
    assert isinstance(items, list)

    if items:
        item = items[0]
        assert item.content_id is not None
        assert item.content_type.value == "STORE_AGENT"
        assert item.searchable_text != ""
        assert item.user_id is None