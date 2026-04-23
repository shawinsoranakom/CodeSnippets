async def test_aindex_with_upsert_kwargs(
    arecord_manager: InMemoryRecordManager, upserting_vector_store: InMemoryVectorStore
) -> None:
    """Test async indexing with upsert_kwargs parameter."""
    mock_aadd_documents = AsyncMock()

    with patch.object(upserting_vector_store, "aadd_documents", mock_aadd_documents):
        docs = [
            Document(
                page_content="Async test document 1",
                metadata={"source": "1"},
            ),
            Document(
                page_content="Async test document 2",
                metadata={"source": "2"},
            ),
        ]

        upsert_kwargs = {"vector_field": "embedding"}

        await aindex(
            docs,
            arecord_manager,
            upserting_vector_store,
            upsert_kwargs=upsert_kwargs,
            key_encoder="sha256",
        )

        # Assert that aadd_documents was called with the correct arguments
        mock_aadd_documents.assert_called_once()
        call_args = mock_aadd_documents.call_args
        assert call_args is not None
        args, kwargs = call_args

        # Check that the documents are correct (ignoring ids)
        assert len(args[0]) == 2
        assert all(isinstance(doc, Document) for doc in args[0])
        assert [doc.page_content for doc in args[0]] == [
            "Async test document 1",
            "Async test document 2",
        ]
        assert [doc.metadata for doc in args[0]] == [{"source": "1"}, {"source": "2"}]

        # Check that IDs are present
        assert "ids" in kwargs
        assert isinstance(kwargs["ids"], list)
        assert len(kwargs["ids"]) == 2

        # Check other arguments
        assert kwargs["batch_size"] == 100
        assert kwargs["vector_field"] == "embedding"