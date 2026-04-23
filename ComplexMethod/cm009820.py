def test_within_batch_deduplication_counting(
    record_manager: InMemoryRecordManager, vector_store: VectorStore
) -> None:
    """Test that within-batch deduplicated documents are counted in num_skipped."""
    # Create documents with within-batch duplicates
    docs = [
        Document(
            page_content="Document A",
            metadata={"source": "1"},
        ),
        Document(
            page_content="Document A",  # Duplicate in same batch
            metadata={"source": "1"},
        ),
        Document(
            page_content="Document B",
            metadata={"source": "2"},
        ),
        Document(
            page_content="Document B",  # Duplicate in same batch
            metadata={"source": "2"},
        ),
        Document(
            page_content="Document C",
            metadata={"source": "3"},
        ),
    ]

    # Index with large batch size to ensure all docs are in one batch
    result = index(
        docs,
        record_manager,
        vector_store,
        batch_size=10,  # All docs in one batch
        cleanup="full",
        key_encoder="sha256",
    )

    # Should have 3 unique documents added
    assert result["num_added"] == 3
    # Should have 2 documents skipped due to within-batch deduplication
    assert result["num_skipped"] == 2
    # Total should match input
    assert result["num_added"] + result["num_skipped"] == len(docs)
    assert result["num_deleted"] == 0
    assert result["num_updated"] == 0

    # Verify the content
    assert isinstance(vector_store, InMemoryVectorStore)
    ids = list(vector_store.store.keys())
    contents = sorted(
        [document.page_content for document in vector_store.get_by_ids(ids)]
    )
    assert contents == ["Document A", "Document B", "Document C"]