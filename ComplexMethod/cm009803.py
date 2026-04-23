def test_translate_grounding_metadata_multiple_chunks() -> None:
    """Test translation with multiple grounding chunks."""
    grounding_metadata = {
        "grounding_chunks": [
            {
                "web": {
                    "uri": "https://example1.com",
                    "title": "Example 1",
                },
                "maps": None,
            },
            {
                "web": None,
                "maps": {
                    "uri": "https://maps.google.com/?cid=123",
                    "title": "Place 1",
                    "placeId": "places/123",
                },
            },
        ],
        "grounding_supports": [
            {
                "segment": {
                    "start_index": 0,
                    "end_index": 10,
                    "text": "First part",
                },
                "grounding_chunk_indices": [0, 1],
                "confidence_scores": [],
            }
        ],
        "web_search_queries": [],
    }

    citations = translate_grounding_metadata_to_citations(grounding_metadata)

    # Should create two citations, one for each chunk
    assert len(citations) == 2

    # First citation from web chunk
    assert citations[0].get("url") == "https://example1.com"
    assert citations[0].get("title") == "Example 1"
    assert "place_id" not in citations[0].get("extras", {})["google_ai_metadata"]

    # Second citation from maps chunk
    assert citations[1].get("url") == "https://maps.google.com/?cid=123"
    assert citations[1].get("title") == "Place 1"
    assert (
        citations[1].get("extras", {})["google_ai_metadata"]["place_id"] == "places/123"
    )