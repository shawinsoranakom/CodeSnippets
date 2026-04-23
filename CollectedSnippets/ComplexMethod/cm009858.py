def test_incremental_delete(
    record_manager: SQLRecordManager,
    vector_store: InMemoryVectorStore,
) -> None:
    """Test indexing with incremental deletion strategy."""
    loader = ToyLoader(
        documents=[
            Document(
                page_content="This is a test document.",
                metadata={"source": "1"},
            ),
            Document(
                page_content="This is another document.",
                metadata={"source": "2"},
            ),
        ],
    )

    with patch.object(
        record_manager,
        "get_time",
        return_value=_JANUARY_SECOND,
    ):
        assert index(
            loader,
            record_manager,
            vector_store,
            cleanup="incremental",
            source_id_key="source",
        ) == {
            "num_added": 2,
            "num_deleted": 0,
            "num_skipped": 0,
            "num_updated": 0,
        }

    doc_texts = {
        # Ignoring type since doc should be in the store and not a None
        vector_store.store.get(uid).page_content  # type: ignore[union-attr]
        for uid in vector_store.store
    }
    assert doc_texts == {"This is another document.", "This is a test document."}

    # Attempt to index again verify that nothing changes
    with patch.object(
        record_manager,
        "get_time",
        return_value=_JANUARY_SECOND,
    ):
        assert index(
            loader,
            record_manager,
            vector_store,
            cleanup="incremental",
            source_id_key="source",
        ) == {
            "num_added": 0,
            "num_deleted": 0,
            "num_skipped": 2,
            "num_updated": 0,
        }

    # Create 2 documents from the same source all with mutated content
    loader = ToyLoader(
        documents=[
            Document(
                page_content="mutated document 1",
                metadata={"source": "1"},
            ),
            Document(
                page_content="mutated document 2",
                metadata={"source": "1"},
            ),
            Document(
                page_content="This is another document.",  # <-- Same as original
                metadata={"source": "2"},
            ),
        ],
    )

    # Attempt to index again verify that nothing changes
    with patch.object(
        record_manager,
        "get_time",
        return_value=datetime(2021, 1, 3, tzinfo=timezone.utc).timestamp(),
    ):
        assert index(
            loader,
            record_manager,
            vector_store,
            cleanup="incremental",
            source_id_key="source",
        ) == {
            "num_added": 2,
            "num_deleted": 1,
            "num_skipped": 1,
            "num_updated": 0,
        }

    doc_texts = {
        # Ignoring type since doc should be in the store and not a None
        vector_store.store.get(uid).page_content  # type: ignore[union-attr]
        for uid in vector_store.store
    }
    assert doc_texts == {
        "mutated document 1",
        "mutated document 2",
        "This is another document.",
    }