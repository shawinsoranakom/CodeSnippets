async def test_inmemory_filter_by_document_id() -> None:
    """Test filtering by document ID field."""
    embedding = DeterministicFakeEmbedding(size=6)
    store = InMemoryVectorStore(embedding=embedding)

    # Add documents with specific IDs using add_documents
    documents = [
        Document(page_content="first document", id="doc_1"),
        Document(page_content="second document", id="doc_2"),
        Document(page_content="third document", id="doc_3"),
    ]
    store.add_documents(documents)

    # Test filtering by specific document ID
    output = store.similarity_search("document", filter=lambda doc: doc.id == "doc_2")
    assert len(output) == 1
    assert output[0].page_content == "second document"
    assert output[0].id == "doc_2"

    # Test async version
    output = await store.asimilarity_search(
        "document", filter=lambda doc: doc.id in {"doc_1", "doc_3"}
    )
    assert len(output) == 2
    ids = {doc.id for doc in output}
    assert ids == {"doc_1", "doc_3"}

    # Test filtering with non-existent ID
    output = store.similarity_search(
        "document", filter=lambda doc: doc.id == "non_existent"
    )
    assert output == []