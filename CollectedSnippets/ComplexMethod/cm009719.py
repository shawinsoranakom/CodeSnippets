async def test_default_aadd_documents(vs_class: type[VectorStore]) -> None:
    """Test delegation to the synchronous method."""
    store = vs_class()

    # Check upsert with id
    assert await store.aadd_documents([Document(id="1", page_content="hello")]) == ["1"]

    assert await store.aget_by_ids(["1"]) == [Document(id="1", page_content="hello")]

    # Check upsert without id
    ids = await store.aadd_documents([Document(page_content="world")])
    assert len(ids) == 1
    assert await store.aget_by_ids(ids) == [Document(id=ids[0], page_content="world")]

    # Check that add_documents works
    assert await store.aadd_documents([Document(id="5", page_content="baz")]) == ["5"]

    # Test add documents with id specified in both document and ids
    original_document = Document(id="7", page_content="baz")
    assert await store.aadd_documents([original_document], ids=["6"]) == ["6"]
    assert original_document.id == "7"  # original document should not be modified
    assert await store.aget_by_ids(["6"]) == [Document(id="6", page_content="baz")]