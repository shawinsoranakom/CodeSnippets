def test_openai_response_headers(use_responses_api: bool) -> None:
    """Test ChatOpenAI response headers."""
    chat_openai = ChatOpenAI(
        include_response_headers=True, use_responses_api=use_responses_api
    )
    query = "I'm Pickle Rick"
    result = chat_openai.invoke(query, max_tokens=MAX_TOKEN_COUNT)  # type: ignore[call-arg]
    headers = result.response_metadata["headers"]
    assert headers
    assert isinstance(headers, dict)
    assert "content-type" in headers

    # Stream
    full: BaseMessageChunk | None = None
    for chunk in chat_openai.stream(query, max_tokens=MAX_TOKEN_COUNT):  # type: ignore[call-arg]
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessage)
    headers = full.response_metadata["headers"]
    assert headers
    assert isinstance(headers, dict)
    assert "content-type" in headers