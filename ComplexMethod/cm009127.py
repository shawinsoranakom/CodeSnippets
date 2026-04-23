def test_incomplete_response() -> None:
    model = ChatOpenAI(
        model=MODEL_NAME, use_responses_api=True, max_completion_tokens=16
    )
    response = model.invoke("Tell me a 100 word story about a bear.")
    assert response.response_metadata["incomplete_details"]
    assert response.response_metadata["incomplete_details"]["reason"]
    assert response.response_metadata["status"] == "incomplete"

    full: AIMessageChunk | None = None
    for chunk in model.stream("Tell me a 100 word story about a bear."):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert full.response_metadata["incomplete_details"]
    assert full.response_metadata["incomplete_details"]["reason"]
    assert full.response_metadata["status"] == "incomplete"