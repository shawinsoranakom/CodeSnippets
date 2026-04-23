async def semantic_search(
    query: str,
    content_types: list[ContentType] | None = None,
    user_id: str | None = None,
    limit: int = 20,
    min_similarity: float = 0.5,
) -> list[dict[str, Any]]:
    """
    Semantic search across content types using embeddings.

    Performs vector similarity search on UnifiedContentEmbedding table.
    Used directly for blocks/docs/library agents, or as the semantic component
    within hybrid_search for store agents.

    If embedding generation fails, falls back to lexical search on searchableText.

    Args:
        query: Search query string
        content_types: List of ContentType to search. Defaults to [BLOCK, STORE_AGENT, DOCUMENTATION]
        user_id: Optional user ID for searching private content (library agents)
        limit: Maximum number of results to return (default: 20)
        min_similarity: Minimum cosine similarity threshold (0-1, default: 0.5)

    Returns:
        List of search results with the following structure:
        [
            {
                "content_id": str,
                "content_type": str,  # "BLOCK", "STORE_AGENT", "DOCUMENTATION", or "LIBRARY_AGENT"
                "searchable_text": str,
                "metadata": dict,
                "similarity": float,  # Cosine similarity score (0-1)
            },
            ...
        ]

    Examples:
        # Search blocks only
        results = await semantic_search("calculate", content_types=[ContentType.BLOCK])

        # Search blocks and documentation
        results = await semantic_search(
            "how to use API",
            content_types=[ContentType.BLOCK, ContentType.DOCUMENTATION]
        )

        # Search all public content (default)
        results = await semantic_search("AI agent")

        # Search user's library agents
        results = await semantic_search(
            "my custom agent",
            content_types=[ContentType.LIBRARY_AGENT],
            user_id="user123"
        )
    """
    # Default to searching all public content types
    if content_types is None:
        content_types = [
            ContentType.BLOCK,
            ContentType.STORE_AGENT,
            ContentType.DOCUMENTATION,
        ]

    # Validate inputs
    if not content_types:
        return []  # Empty content_types would cause invalid SQL (IN ())

    query = query.strip()
    if not query:
        return []

    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100

    # Generate query embedding
    try:
        query_embedding = await embed_query(query)
        # Semantic search with embeddings
        embedding_str = embedding_to_vector_string(query_embedding)

        # Build params in order: limit, then user_id (if provided), then content types
        params: list[Any] = [limit]
        user_filter = ""
        if user_id is not None:
            user_filter = 'AND "userId" = ${}'.format(len(params) + 1)
            params.append(user_id)

        # Add content type parameters and build placeholders dynamically
        content_type_start_idx = len(params) + 1
        content_type_placeholders = ", ".join(
            "$" + str(content_type_start_idx + i) + '::{schema_prefix}"ContentType"'
            for i in range(len(content_types))
        )
        params.extend([ct.value for ct in content_types])

        # Build min_similarity param index before appending
        min_similarity_idx = len(params) + 1
        params.append(min_similarity)

        # Use unqualified ::vector and <=> operator - pgvector is in search_path on all environments
        sql = (
            """
            SELECT
                "contentId" as content_id,
                "contentType" as content_type,
                "searchableText" as searchable_text,
                metadata,
                1 - (embedding <=> '"""
            + embedding_str
            + """'::vector) as similarity
            FROM {schema_prefix}"UnifiedContentEmbedding"
            WHERE "contentType" IN ("""
            + content_type_placeholders
            + """)
            """
            + user_filter
            + """
            AND 1 - (embedding <=> '"""
            + embedding_str
            + """'::vector) >= $"""
            + str(min_similarity_idx)
            + """
            ORDER BY similarity DESC
            LIMIT $1
        """
        )

        results = await query_raw_with_schema(sql, *params)
        return [
            {
                "content_id": row["content_id"],
                "content_type": row["content_type"],
                "searchable_text": row["searchable_text"],
                "metadata": row["metadata"],
                "similarity": float(row["similarity"]),
            }
            for row in results
        ]
    except Exception as e:
        logger.warning(f"Semantic search failed, falling back to lexical search: {e}")

    # Fallback to lexical search if embeddings unavailable

    params_lexical: list[Any] = [limit]
    user_filter = ""
    if user_id is not None:
        user_filter = 'AND "userId" = ${}'.format(len(params_lexical) + 1)
        params_lexical.append(user_id)

    # Add content type parameters and build placeholders dynamically
    content_type_start_idx = len(params_lexical) + 1
    content_type_placeholders_lexical = ", ".join(
        "$" + str(content_type_start_idx + i) + '::{schema_prefix}"ContentType"'
        for i in range(len(content_types))
    )
    params_lexical.extend([ct.value for ct in content_types])

    # Build query param index before appending
    query_param_idx = len(params_lexical) + 1
    params_lexical.append(f"%{query}%")

    # Use regular string (not f-string) for template to preserve {schema_prefix} placeholders
    sql_lexical = (
        """
        SELECT
            "contentId" as content_id,
            "contentType" as content_type,
            "searchableText" as searchable_text,
            metadata,
            0.0 as similarity
        FROM {schema_prefix}"UnifiedContentEmbedding"
        WHERE "contentType" IN ("""
        + content_type_placeholders_lexical
        + """)
        """
        + user_filter
        + """
        AND "searchableText" ILIKE $"""
        + str(query_param_idx)
        + """
        ORDER BY "updatedAt" DESC
        LIMIT $1
    """
    )

    try:
        results = await query_raw_with_schema(sql_lexical, *params_lexical)
        return [
            {
                "content_id": row["content_id"],
                "content_type": row["content_type"],
                "searchable_text": row["searchable_text"],
                "metadata": row["metadata"],
                "similarity": 0.0,  # Lexical search doesn't provide similarity
            }
            for row in results
        ]
    except Exception as e:
        logger.error(f"Lexical search failed: {e}")
        return []