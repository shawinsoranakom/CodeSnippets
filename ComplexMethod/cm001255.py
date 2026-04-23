def bm25_rerank(
    query: str,
    results: list[dict[str, Any]],
    text_field: str = "searchable_text",
    bm25_weight: float = 0.3,
    original_score_field: str = "combined_score",
) -> list[dict[str, Any]]:
    """
    Rerank search results using BM25.

    Combines the original combined_score with BM25 score for improved
    lexical relevance, especially for exact term matches.

    Args:
        query: The search query
        results: List of result dicts with text_field and original_score_field
        text_field: Field name containing the text to score
        bm25_weight: Weight for BM25 score (0-1). Original score gets (1 - bm25_weight)
        original_score_field: Field name containing the original score

    Returns:
        Results list sorted by combined score (BM25 + original)
    """
    if not results or not query:
        return results

    # Extract texts and tokenize
    corpus = [tokenize(r.get(text_field, "") or "") for r in results]

    # Handle edge case where all documents are empty
    if all(len(doc) == 0 for doc in corpus):
        return results

    # Build BM25 index
    bm25 = BM25Okapi(corpus)

    # Score query against corpus
    query_tokens = tokenize(query)
    if not query_tokens:
        return results

    bm25_scores = bm25.get_scores(query_tokens)

    # Normalize BM25 scores to 0-1 range
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
    normalized_bm25 = [s / max_bm25 for s in bm25_scores]

    # Combine scores
    original_weight = 1.0 - bm25_weight
    for i, result in enumerate(results):
        original_score = result.get(original_score_field, 0) or 0
        result["bm25_score"] = normalized_bm25[i]
        final_score = (
            original_weight * original_score + bm25_weight * normalized_bm25[i]
        )
        result["final_score"] = final_score
        result["relevance"] = final_score

    # Sort by relevance descending
    results.sort(key=lambda x: x.get("relevance", 0), reverse=True)

    return results