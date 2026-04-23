def test_translate_grounding_metadata_maps() -> None:
    """Test translation of maps grounding metadata to citations."""
    grounding_metadata = {
        "grounding_chunks": [
            {
                "web": None,
                "maps": {
                    "uri": "https://maps.google.com/?cid=13100894621228039586",
                    "title": "Heaven on 7th Marketplace",
                    "placeId": "places/ChIJ0-zA1vBZwokRon0fGj-6z7U",
                },
            }
        ],
        "grounding_supports": [
            {
                "segment": {
                    "start_index": 0,
                    "end_index": 25,
                    "text": "Great Italian restaurant",
                },
                "grounding_chunk_indices": [0],
                "confidence_scores": [0.95],
            }
        ],
        "web_search_queries": [],
    }

    citations = translate_grounding_metadata_to_citations(grounding_metadata)

    assert len(citations) == 1
    citation = citations[0]
    assert citation["type"] == "citation"
    assert citation.get("url") == "https://maps.google.com/?cid=13100894621228039586"
    assert citation.get("title") == "Heaven on 7th Marketplace"
    assert citation.get("start_index") == 0
    assert citation.get("end_index") == 25
    assert citation.get("cited_text") == "Great Italian restaurant"

    extras = citation.get("extras", {})["google_ai_metadata"]
    assert extras["web_search_queries"] == []
    assert extras["grounding_chunk_index"] == 0
    assert extras["confidence_scores"] == [0.95]
    assert extras["place_id"] == "places/ChIJ0-zA1vBZwokRon0fGj-6z7U"