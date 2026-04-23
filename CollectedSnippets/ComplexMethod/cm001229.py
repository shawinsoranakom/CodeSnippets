async def test_unified_hybrid_search_pagination(
    server,
    mock_embedding: list[float],
    cleanup_embeddings: list,
):
    """Test unified search pagination works correctly."""
    # Use a unique search term to avoid matching other test data
    unique_term = f"xyzpagtest{uuid.uuid4().hex[:8]}"

    # Create multiple items
    content_ids = []
    for i in range(5):
        content_id = f"test-pagination-{uuid.uuid4()}"
        content_ids.append(content_id)
        cleanup_embeddings.append((ContentType.BLOCK, content_id, None))

        await embeddings.store_content_embedding(
            content_type=ContentType.BLOCK,
            content_id=content_id,
            embedding=mock_embedding,
            searchable_text=f"{unique_term} item number {i}",
            metadata={"index": i},
            user_id=None,
        )

    # Get first page
    page1_results, total1 = await unified_hybrid_search(
        query=unique_term,
        content_types=[ContentType.BLOCK],
        page=1,
        page_size=2,
    )

    # Get second page
    page2_results, total2 = await unified_hybrid_search(
        query=unique_term,
        content_types=[ContentType.BLOCK],
        page=2,
        page_size=2,
    )

    # Total should be consistent
    assert total1 == total2

    # Pages should have different content (if we have enough results)
    if len(page1_results) > 0 and len(page2_results) > 0:
        page1_ids = {r["content_id"] for r in page1_results}
        page2_ids = {r["content_id"] for r in page2_results}
        # No overlap between pages
        assert page1_ids.isdisjoint(page2_ids)