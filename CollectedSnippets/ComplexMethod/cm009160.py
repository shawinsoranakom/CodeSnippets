def test_stream() -> None:
    """Test streaming tokens from OpenAI."""
    llm = ChatOpenAI(
        model="gpt-5-nano",
        service_tier="flex",  # Also test service_tier
        max_retries=3,  # Add retries for 503 capacity errors
    )

    full: BaseMessageChunk | None = None
    for chunk in llm.stream("I'm Pickle Rick"):
        assert isinstance(chunk.content, str)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert full.response_metadata.get("finish_reason") is not None
    assert full.response_metadata.get("model_name") is not None

    # check token usage
    aggregate: BaseMessageChunk | None = None
    chunks_with_token_counts = 0
    chunks_with_response_metadata = 0
    for chunk in llm.stream("Hello"):
        assert isinstance(chunk.content, str)
        aggregate = chunk if aggregate is None else aggregate + chunk
        assert isinstance(chunk, AIMessageChunk)
        if chunk.usage_metadata is not None:
            chunks_with_token_counts += 1
        if chunk.response_metadata and not set(chunk.response_metadata.keys()).issubset(
            {"model_provider", "output_version"}
        ):
            chunks_with_response_metadata += 1
    if chunks_with_token_counts != 1 or chunks_with_response_metadata != 1:
        msg = (
            "Expected exactly one chunk with metadata. "
            "AIMessageChunk aggregation can add these metadata. Check that "
            "this is behaving properly."
        )
        raise AssertionError(msg)
    assert isinstance(aggregate, AIMessageChunk)
    assert aggregate.usage_metadata is not None
    assert aggregate.usage_metadata["input_tokens"] > 0
    assert aggregate.usage_metadata["output_tokens"] > 0
    assert aggregate.usage_metadata["total_tokens"] > 0
    assert aggregate.usage_metadata.get("input_token_details", {}).get("flex", 0) > 0  # type: ignore[operator]
    assert aggregate.usage_metadata.get("output_token_details", {}).get("flex", 0) > 0  # type: ignore[operator]
    assert (
        aggregate.usage_metadata.get("output_token_details", {}).get(  # type: ignore[operator]
            "flex_reasoning", 0
        )
        > 0
    )
    assert aggregate.usage_metadata.get("output_token_details", {}).get(  # type: ignore[operator]
        "flex_reasoning", 0
    ) + aggregate.usage_metadata.get("output_token_details", {}).get(
        "flex", 0
    ) == aggregate.usage_metadata.get("output_tokens")