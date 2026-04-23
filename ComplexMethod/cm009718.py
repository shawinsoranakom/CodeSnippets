def test_default_add_documents(vs_class: type[VectorStore]) -> None:
    """Test default implementation of add_documents.

    Test that we can implement the upsert method of the CustomVectorStore
    class without violating the Liskov Substitution Principle.
    """
    store = vs_class()

    # Check upsert with id
    assert store.add_documents([Document(id="1", page_content="hello")]) == ["1"]

    assert store.get_by_ids(["1"]) == [Document(id="1", page_content="hello")]

    # Check upsert without id
    ids = store.add_documents([Document(page_content="world")])
    assert len(ids) == 1
    assert store.get_by_ids(ids) == [Document(id=ids[0], page_content="world")]

    # Check that add_documents works
    assert store.add_documents([Document(id="5", page_content="baz")]) == ["5"]

    # Test add documents with id specified in both document and ids
    original_document = Document(id="7", page_content="baz")
    assert store.add_documents([original_document], ids=["6"]) == ["6"]
    assert original_document.id == "7"  # original document should not be modified
    assert store.get_by_ids(["6"]) == [Document(id="6", page_content="baz")]