def test_incremental_delete_with_batch_size(
    record_manager: SQLRecordManager,
    vector_store: InMemoryVectorStore,
) -> None:
    """Test indexing with incremental deletion strategy and batch size."""
    loader = ToyLoader(
        documents=[
            Document(
                page_content="1",
                metadata={"source": "1"},
            ),
            Document(
                page_content="2",
                metadata={"source": "2"},
            ),
            Document(
                page_content="3",
                metadata={"source": "3"},
            ),
            Document(
                page_content="4",
                metadata={"source": "4"},
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
            batch_size=3,
        ) == {
            "num_added": 4,
            "num_deleted": 0,
            "num_skipped": 0,
            "num_updated": 0,
        }

    doc_texts = {
        # Ignoring type since doc should be in the store and not a None
        vector_store.store.get(uid).page_content  # type: ignore[union-attr]
        for uid in vector_store.store
    }
    assert doc_texts == {"1", "2", "3", "4"}

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
            batch_size=3,
        ) == {
            "num_added": 0,
            "num_deleted": 0,
            "num_skipped": 4,
            "num_updated": 0,
        }

    # Attempt to index again verify that nothing changes
    with patch.object(
        record_manager,
        "get_time",
        return_value=datetime(2022, 1, 3, tzinfo=timezone.utc).timestamp(),
    ):
        # Docs with same content
        docs = [
            Document(
                page_content="1",
                metadata={"source": "1"},
            ),
            Document(
                page_content="2",
                metadata={"source": "2"},
            ),
        ]
        assert index(
            docs,
            record_manager,
            vector_store,
            cleanup="incremental",
            source_id_key="source",
            batch_size=1,
        ) == {
            "num_added": 0,
            "num_deleted": 0,
            "num_skipped": 2,
            "num_updated": 0,
        }

    # Attempt to index again verify that nothing changes
    with patch.object(
        record_manager,
        "get_time",
        return_value=datetime(2023, 1, 3, tzinfo=timezone.utc).timestamp(),
    ):
        # Docs with same content
        docs = [
            Document(
                page_content="1",
                metadata={"source": "1"},
            ),
            Document(
                page_content="2",
                metadata={"source": "2"},
            ),
        ]
        assert index(
            docs,
            record_manager,
            vector_store,
            cleanup="incremental",
            source_id_key="source",
            batch_size=1,
        ) == {
            "num_added": 0,
            "num_deleted": 0,
            "num_skipped": 2,
            "num_updated": 0,
        }

    # Try to index with changed docs now
    with patch.object(
        record_manager,
        "get_time",
        return_value=datetime(2024, 1, 3, tzinfo=timezone.utc).timestamp(),
    ):
        # Docs with same content
        docs = [
            Document(
                page_content="changed 1",
                metadata={"source": "1"},
            ),
            Document(
                page_content="changed 2",
                metadata={"source": "2"},
            ),
        ]
        assert index(
            docs,
            record_manager,
            vector_store,
            cleanup="incremental",
            source_id_key="source",
        ) == {
            "num_added": 2,
            "num_deleted": 2,
            "num_skipped": 0,
            "num_updated": 0,
        }