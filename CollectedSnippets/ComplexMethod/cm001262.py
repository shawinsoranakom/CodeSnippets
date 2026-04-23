async def test_get_embedding_stats_all_types():
    """Test get_embedding_stats aggregates all content types."""
    stats = await get_embedding_stats()

    # Should have structure with by_type and totals
    assert "by_type" in stats
    assert "totals" in stats

    # Check each content type is present
    by_type = stats["by_type"]
    assert "STORE_AGENT" in by_type
    assert "BLOCK" in by_type
    assert "DOCUMENTATION" in by_type

    # Check totals are aggregated
    totals = stats["totals"]
    assert totals["total"] >= 0
    assert totals["with_embeddings"] >= 0
    assert totals["without_embeddings"] >= 0
    assert "coverage_percent" in totals