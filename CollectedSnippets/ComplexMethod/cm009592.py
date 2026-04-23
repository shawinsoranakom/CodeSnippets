def translate_grounding_metadata_to_citations(
    grounding_metadata: dict[str, Any],
) -> list[Citation]:
    """Translate Google AI grounding metadata to LangChain Citations.

    Args:
        grounding_metadata: Google AI grounding metadata containing web search
            queries, grounding chunks, and grounding supports.

    Returns:
        List of Citation content blocks derived from the grounding metadata.

    Example:
        >>> metadata = {
        ...     "web_search_queries": ["UEFA Euro 2024 winner"],
        ...     "grounding_chunks": [
        ...         {
        ...             "web": {
        ...                 "uri": "https://uefa.com/euro2024",
        ...                 "title": "UEFA Euro 2024 Results",
        ...             }
        ...         }
        ...     ],
        ...     "grounding_supports": [
        ...         {
        ...             "segment": {
        ...                 "start_index": 0,
        ...                 "end_index": 47,
        ...                 "text": "Spain won the UEFA Euro 2024 championship",
        ...             },
        ...             "grounding_chunk_indices": [0],
        ...         }
        ...     ],
        ... }
        >>> citations = translate_grounding_metadata_to_citations(metadata)
        >>> len(citations)
        1
        >>> citations[0]["url"]
        'https://uefa.com/euro2024'
    """
    if not grounding_metadata:
        return []

    grounding_chunks = grounding_metadata.get("grounding_chunks", [])
    grounding_supports = grounding_metadata.get("grounding_supports", [])
    web_search_queries = grounding_metadata.get("web_search_queries", [])

    citations: list[Citation] = []

    for support in grounding_supports:
        segment = support.get("segment", {})
        chunk_indices = support.get("grounding_chunk_indices", [])

        start_index = segment.get("start_index")
        end_index = segment.get("end_index")
        cited_text = segment.get("text")

        # Create a citation for each referenced chunk
        for chunk_index in chunk_indices:
            if chunk_index < len(grounding_chunks):
                chunk = grounding_chunks[chunk_index]

                # Handle web and maps grounding
                web_info = chunk.get("web") or {}
                maps_info = chunk.get("maps") or {}

                # Extract citation info depending on source
                url = maps_info.get("uri") or web_info.get("uri")
                title = maps_info.get("title") or web_info.get("title")

                # Note: confidence_scores is a legacy field from Gemini 2.0 and earlier
                # that indicated confidence (0.0-1.0) for each grounding chunk.
                #
                # In Gemini 2.5+, this field is always None/empty and should be ignored.
                extras_metadata = {
                    "web_search_queries": web_search_queries,
                    "grounding_chunk_index": chunk_index,
                    "confidence_scores": support.get("confidence_scores") or [],
                }

                # Add maps-specific metadata if present
                if maps_info.get("placeId"):
                    extras_metadata["place_id"] = maps_info["placeId"]

                citation = create_citation(
                    url=url,
                    title=title,
                    start_index=start_index,
                    end_index=end_index,
                    cited_text=cited_text,
                    google_ai_metadata=extras_metadata,
                )
                citations.append(citation)

    return citations