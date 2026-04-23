def test_index_with_upsert_kwargs(
    record_manager: InMemoryRecordManager, upserting_vector_store: InMemoryVectorStore
) -> None:
    """Test indexing with upsert_kwargs parameter."""
    mock_add_documents = MagicMock()

    with patch.object(upserting_vector_store, "add_documents", mock_add_documents):
        docs = [
            Document(
                page_content="Test document 1",
                metadata={"source": "1"},
            ),
            Document(
                page_content="Test document 2",
                metadata={"source": "2"},
            ),
        ]

        upsert_kwargs = {"vector_field": "embedding"}

        index(
            docs,
            record_manager,
            upserting_vector_store,
            upsert_kwargs=upsert_kwargs,
            key_encoder="sha256",
        )

        # Assert that add_documents was called with the correct arguments
        mock_add_documents.assert_called_once()
        call_args = mock_add_documents.call_args
        assert call_args is not None
        args, kwargs = call_args

        # Check that the documents are correct (ignoring ids)
        assert len(args[0]) == 2
        assert all(isinstance(doc, Document) for doc in args[0])
        assert [doc.page_content for doc in args[0]] == [
            "Test document 1",
            "Test document 2",
        ]
        assert [doc.metadata for doc in args[0]] == [{"source": "1"}, {"source": "2"}]

        # Check that IDs are present
        assert "ids" in kwargs
        assert isinstance(kwargs["ids"], list)
        assert len(kwargs["ids"]) == 2

        # Check other arguments
        assert kwargs["batch_size"] == 100
        assert kwargs["vector_field"] == "embedding"