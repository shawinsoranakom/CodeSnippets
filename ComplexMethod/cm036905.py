async def test_rerank_api_query_text_vs_docs_image(server: RemoteOpenAIServer):
    query = "Describe the red object"

    red_image = make_base64_image(64, 64, color=(255, 0, 0))
    blue_image = make_base64_image(64, 64, color=(0, 0, 255))

    documents = [
        make_image_mm_param(red_image),
        make_image_mm_param(blue_image),
    ]

    rerank_response = requests.post(
        server.url_for("rerank"),
        json={"model": MODEL_NAME, "query": query, "documents": documents},
    )

    rerank_response.raise_for_status()
    rerank = RerankResponse.model_validate(rerank_response.json())

    assert rerank.id is not None
    assert rerank.results is not None
    assert len(rerank.results) == 2

    red_result = next(r for r in rerank.results if r.index == 0)
    blue_result = next(r for r in rerank.results if r.index == 1)

    assert red_result.relevance_score > blue_result.relevance_score