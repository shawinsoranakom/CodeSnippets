async def test_documentation_handler_real_fs():
    """Test DocumentationHandler with real filesystem."""
    handler = DocumentationHandler()

    # Get stats from real filesystem
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

    # Items should be list
    assert isinstance(items, list)

    if items:
        item = items[0]
        assert item.content_id is not None  # Should be relative path
        assert item.content_type.value == "DOCUMENTATION"
        assert item.searchable_text != ""
        assert item.user_id is None