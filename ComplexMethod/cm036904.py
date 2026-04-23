async def test_rerank_api_texts(server: RemoteOpenAIServer):
    """Test ColBERT rerank endpoint."""
    query = "What is the capital of France?"
    documents = [
        "The capital of Brazil is Brasilia.",
        "The capital of France is Paris.",
    ]

    rerank_response = requests.post(
        server.url_for("rerank"),
        json={
            "model": MODEL_NAME,
            "query": query,
            "documents": documents,
        },
    )
    rerank_response.raise_for_status()
    rerank = RerankResponse.model_validate(rerank_response.json())

    assert rerank.id is not None
    assert rerank.results is not None
    assert len(rerank.results) == 2

    paris_result = next(r for r in rerank.results if r.index == 1)
    brazil_result = next(r for r in rerank.results if r.index == 0)

    assert paris_result.relevance_score > brazil_result.relevance_score