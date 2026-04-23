async def test_rerank_api_query_image_vs_docs_text(server: RemoteOpenAIServer):
    red_image = make_base64_image(64, 64, color=(255, 0, 0))
    image_query = make_image_mm_param(red_image, text="red color")

    documents = [
        "Describe the red object.",
        "The capital of France is Paris.",
    ]

    rerank_response = requests.post(
        server.url_for("rerank"),
        json={
            "model": MODEL_NAME,
            "query": image_query,
            "documents": documents,
        },
    )
    rerank_response.raise_for_status()
    rerank = RerankResponse.model_validate(rerank_response.json())

    assert rerank.id is not None
    assert rerank.results is not None
    assert len(rerank.results) == 2

    result0 = next(r for r in rerank.results if r.index == 0)
    result1 = next(r for r in rerank.results if r.index == 1)

    assert result0.relevance_score > result1.relevance_score