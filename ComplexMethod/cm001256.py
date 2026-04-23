async def unified_hybrid_search(
    query: str,
    content_types: list[ContentType] | None = None,
    category: str | None = None,
    page: int = 1,
    page_size: int = 20,
    weights: UnifiedSearchWeights | None = None,
    min_score: float | None = None,
    user_id: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """
    Unified hybrid search across all content types.

    Searches UnifiedContentEmbedding using both semantic (vector) and lexical (tsvector) signals.

    Args:
        query: Search query string
        content_types: List of content types to search. Defaults to all public types.
        category: Filter by category (for content types that support it)
        page: Page number (1-indexed)
        page_size: Results per page
        weights: Custom weights for search signals
        min_score: Minimum relevance score threshold (0-1)
        user_id: User ID for searching private content (library agents)

    Returns:
        Tuple of (results list, total count)
    """
    # Validate inputs
    query = query.strip()
    if not query:
        return [], 0

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 100:
        page_size = 100

    if content_types is None:
        content_types = [
            ContentType.STORE_AGENT,
            ContentType.BLOCK,
            ContentType.DOCUMENTATION,
        ]

    if weights is None:
        weights = DEFAULT_UNIFIED_WEIGHTS
    if min_score is None:
        min_score = DEFAULT_MIN_SCORE

    offset = (page - 1) * page_size

    # Generate query embedding with graceful degradation
    try:
        query_embedding = await embed_query(query)
    except Exception as e:
        logger.warning(
            f"Failed to generate query embedding - falling back to lexical-only search: {e}. "
            "Check that openai_internal_api_key is configured and OpenAI API is accessible."
        )
        query_embedding = [0.0] * EMBEDDING_DIM
        # Redistribute semantic weight to lexical
        total_non_semantic = weights.lexical + weights.category + weights.recency
        if total_non_semantic > 0:
            factor = 1.0 / total_non_semantic
            weights = UnifiedSearchWeights(
                semantic=0.0,
                lexical=weights.lexical * factor,
                category=weights.category * factor,
                recency=weights.recency * factor,
            )
        else:
            weights = UnifiedSearchWeights(
                semantic=0.0, lexical=1.0, category=0.0, recency=0.0
            )

    # Build parameters
    params: list[Any] = []
    param_idx = 1

    # Query for lexical search
    params.append(query)
    query_param = f"${param_idx}"
    param_idx += 1

    # Query lowercase for category matching
    params.append(query.lower())
    query_lower_param = f"${param_idx}"
    param_idx += 1

    # Embedding
    embedding_str = embedding_to_vector_string(query_embedding)
    params.append(embedding_str)
    embedding_param = f"${param_idx}"
    param_idx += 1

    # Content types
    content_type_values = [ct.value for ct in content_types]
    params.append(content_type_values)
    content_types_param = f"${param_idx}"
    param_idx += 1

    # User ID filter (for private content)
    user_filter = ""
    if user_id is not None:
        params.append(user_id)
        user_filter = f'AND (uce."userId" = ${param_idx} OR uce."userId" IS NULL)'
        param_idx += 1
    else:
        user_filter = 'AND uce."userId" IS NULL'

    # Weights
    params.append(weights.semantic)
    w_semantic = f"${param_idx}"
    param_idx += 1

    params.append(weights.lexical)
    w_lexical = f"${param_idx}"
    param_idx += 1

    params.append(weights.category)
    w_category = f"${param_idx}"
    param_idx += 1

    params.append(weights.recency)
    w_recency = f"${param_idx}"
    param_idx += 1

    # Min score
    params.append(min_score)
    min_score_param = f"${param_idx}"
    param_idx += 1

    # Pagination
    params.append(page_size)
    limit_param = f"${param_idx}"
    param_idx += 1

    params.append(offset)
    offset_param = f"${param_idx}"
    param_idx += 1

    # Unified search query on UnifiedContentEmbedding
    sql_query = f"""
        WITH candidates AS (
            -- Lexical matches (uses GIN index on search column)
            SELECT uce.id, uce."contentType", uce."contentId"
            FROM {{schema_prefix}}"UnifiedContentEmbedding" uce
            WHERE uce."contentType" = ANY({content_types_param}::{{schema_prefix}}"ContentType"[])
            {user_filter}
            AND uce.search @@ plainto_tsquery('english', {query_param})

            UNION

            -- Semantic matches (uses HNSW index on embedding)
            (
                SELECT uce.id, uce."contentType", uce."contentId"
                FROM {{schema_prefix}}"UnifiedContentEmbedding" uce
                WHERE uce."contentType" = ANY({content_types_param}::{{schema_prefix}}"ContentType"[])
                {user_filter}
                ORDER BY uce.embedding <=> {embedding_param}::vector
                LIMIT 200
            )
        ),
        search_scores AS (
            SELECT
                uce."contentType" as content_type,
                uce."contentId" as content_id,
                uce."searchableText" as searchable_text,
                uce.metadata,
                uce."updatedAt" as updated_at,
                -- Semantic score: cosine similarity (1 - distance)
                COALESCE(1 - (uce.embedding <=> {embedding_param}::vector), 0) as semantic_score,
                -- Lexical score: ts_rank_cd
                COALESCE(ts_rank_cd(uce.search, plainto_tsquery('english', {query_param})), 0) as lexical_raw,
                -- Category match from metadata
                CASE
                    WHEN uce.metadata ? 'categories' AND EXISTS (
                        SELECT 1 FROM jsonb_array_elements_text(uce.metadata->'categories') cat
                        WHERE LOWER(cat) LIKE '%' || {query_lower_param} || '%'
                    )
                    THEN 1.0
                    ELSE 0.0
                END as category_score,
                -- Recency score: linear decay over 90 days
                GREATEST(0, 1 - EXTRACT(EPOCH FROM (NOW() - uce."updatedAt")) / (90 * 24 * 3600)) as recency_score
            FROM candidates c
            INNER JOIN {{schema_prefix}}"UnifiedContentEmbedding" uce ON c.id = uce.id
        ),
        max_lexical AS (
            SELECT GREATEST(MAX(lexical_raw), 0.001) as max_val FROM search_scores
        ),
        normalized AS (
            SELECT
                ss.*,
                ss.lexical_raw / ml.max_val as lexical_score
            FROM search_scores ss
            CROSS JOIN max_lexical ml
        ),
        scored AS (
            SELECT
                content_type,
                content_id,
                searchable_text,
                metadata,
                updated_at,
                semantic_score,
                lexical_score,
                category_score,
                recency_score,
                (
                    {w_semantic} * semantic_score +
                    {w_lexical} * lexical_score +
                    {w_category} * category_score +
                    {w_recency} * recency_score
                ) as combined_score
            FROM normalized
        ),
        filtered AS (
            SELECT *, COUNT(*) OVER () as total_count
            FROM scored
            WHERE combined_score >= {min_score_param}
        )
        SELECT * FROM filtered
        ORDER BY combined_score DESC
        LIMIT {limit_param} OFFSET {offset_param}
    """

    try:
        results = await query_raw_with_schema(sql_query, *params)
    except Exception as e:
        await _log_vector_error_diagnostics(e)
        raise

    total = results[0]["total_count"] if results else 0
    # Apply BM25 reranking
    if results:
        results = bm25_rerank(
            query=query,
            results=results,
            text_field="searchable_text",
            bm25_weight=0.3,
            original_score_field="combined_score",
        )

    # Clean up results
    for result in results:
        result.pop("total_count", None)

    logger.info(f"Unified hybrid search: {len(results)} results, {total} total")

    return results, total