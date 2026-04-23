def test_chroma_handles_none_page_content_with_vectors() -> None:
    """Test that Chroma gracefully handles None page_content values with vectors."""
    from langchain_chroma.vectorstores import _results_to_docs_and_vectors

    mock_results = {
        "documents": [["valid content", None, "another valid content"]],
        "metadatas": [[{"key": "value1"}, {"key": "value2"}, {"key": "value3"}]],
        "ids": [["id1", "id2", "id3"]],
        "embeddings": [[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]],
    }
    docs_and_vectors = _results_to_docs_and_vectors(mock_results)

    assert len(docs_and_vectors) == 2
    assert docs_and_vectors[0][0].page_content == "valid content"
    assert docs_and_vectors[1][0].page_content == "another valid content"
    assert docs_and_vectors[0][0].id == "id1"
    assert docs_and_vectors[1][0].id == "id3"
    assert docs_and_vectors[0][1] == [0.1, 0.2]
    assert docs_and_vectors[1][1] == [0.5, 0.6]