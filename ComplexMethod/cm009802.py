def test_translate_grounding_metadata_none() -> None:
    """Test translation when both web and maps are None."""
    grounding_metadata = {
        "grounding_chunks": [
            {
                "web": None,
                "maps": None,
            }
        ],
        "grounding_supports": [
            {
                "segment": {
                    "start_index": 0,
                    "end_index": 10,
                    "text": "test text",
                },
                "grounding_chunk_indices": [0],
                "confidence_scores": [],
            }
        ],
        "web_search_queries": [],
    }

    citations = translate_grounding_metadata_to_citations(grounding_metadata)

    # Should still create citation but without url/title fields when None
    assert len(citations) == 1
    citation = citations[0]
    assert citation["type"] == "citation"
    # url and title are omitted when None
    assert "url" not in citation
    assert "title" not in citation
    assert citation.get("start_index") == 0
    assert citation.get("end_index") == 10
    assert citation.get("cited_text") == "test text"