def test_translate_grounding_metadata_web() -> None:
    """Test translation of web grounding metadata to citations."""
    grounding_metadata = {
        "grounding_chunks": [
            {
                "web": {
                    "uri": "https://example.com",
                    "title": "Example Site",
                },
                "maps": None,
            }
        ],
        "grounding_supports": [
            {
                "segment": {
                    "start_index": 0,
                    "end_index": 13,
                    "text": "Test response",
                },
                "grounding_chunk_indices": [0],
                "confidence_scores": [],
            }
        ],
        "web_search_queries": ["test query"],
    }

    citations = translate_grounding_metadata_to_citations(grounding_metadata)

    assert len(citations) == 1
    citation = citations[0]
    assert citation["type"] == "citation"
    assert citation.get("url") == "https://example.com"
    assert citation.get("title") == "Example Site"
    assert citation.get("start_index") == 0
    assert citation.get("end_index") == 13
    assert citation.get("cited_text") == "Test response"

    extras = citation.get("extras", {})["google_ai_metadata"]
    assert extras["web_search_queries"] == ["test query"]
    assert extras["grounding_chunk_index"] == 0
    assert "place_id" not in extras