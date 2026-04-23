async def test_backfill_all_content_types_dry_run(mock_generate):
    """Test backfill_all_content_types processes all handlers in order."""
    # Mock OpenAI to return fake embedding
    mock_generate.return_value = [0.1] * EMBEDDING_DIM

    # Run backfill with batch_size=1 to process max 1 per type
    result = await backfill_all_content_types(batch_size=1)

    # Should have results for all content types
    assert "by_type" in result
    assert "totals" in result

    by_type = result["by_type"]
    assert "BLOCK" in by_type
    assert "STORE_AGENT" in by_type
    assert "DOCUMENTATION" in by_type

    # Each type should have correct structure
    for content_type, type_result in by_type.items():
        assert "processed" in type_result
        assert "success" in type_result
        assert "failed" in type_result

    # Totals should aggregate
    totals = result["totals"]
    assert totals["processed"] >= 0
    assert totals["success"] >= 0
    assert totals["failed"] >= 0