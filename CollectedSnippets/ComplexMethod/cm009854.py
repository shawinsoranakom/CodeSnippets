def test_invoke(
    time_weighted_retriever: TimeWeightedVectorStoreRetriever,
) -> None:
    query = "Test query"
    relevant_documents = time_weighted_retriever.invoke(query)
    want = [(doc, 0.5) for doc in _get_example_memories()]
    assert isinstance(relevant_documents, list)
    assert len(relevant_documents) == len(want)
    now = datetime.now()
    for doc in relevant_documents:
        # assert that the last_accessed_at is close to now.
        assert now - timedelta(hours=1) < doc.metadata["last_accessed_at"] <= now

    # assert that the last_accessed_at in the memory stream is updated.
    for d in time_weighted_retriever.memory_stream:
        assert now - timedelta(hours=1) < d.metadata["last_accessed_at"] <= now