def test_stream() -> None:
    """Test streaming tokens from Anthropic."""
    llm = ChatAnthropic(model_name=MODEL_NAME)  # type: ignore[call-arg, call-arg]

    full: BaseMessageChunk | None = None
    chunks_with_input_token_counts = 0
    chunks_with_output_token_counts = 0
    chunks_with_model_name = 0
    for token in llm.stream("I'm Pickle Rick"):
        assert isinstance(token.content, str)
        full = cast("BaseMessageChunk", token) if full is None else full + token
        assert isinstance(token, AIMessageChunk)
        if token.usage_metadata is not None:
            if token.usage_metadata.get("input_tokens"):
                chunks_with_input_token_counts += 1
            if token.usage_metadata.get("output_tokens"):
                chunks_with_output_token_counts += 1
        chunks_with_model_name += int("model_name" in token.response_metadata)
    if chunks_with_input_token_counts != 1 or chunks_with_output_token_counts != 1:
        msg = (
            "Expected exactly one chunk with input or output token counts. "
            "AIMessageChunk aggregation adds counts. Check that "
            "this is behaving properly."
        )
        raise AssertionError(
            msg,
        )
    assert chunks_with_model_name == 1
    # check token usage is populated
    assert isinstance(full, AIMessageChunk)
    assert len(full.content_blocks) == 1
    assert full.content_blocks[0]["type"] == "text"
    assert full.content_blocks[0]["text"]
    assert full.usage_metadata is not None
    assert full.usage_metadata["input_tokens"] > 0
    assert full.usage_metadata["output_tokens"] > 0
    assert full.usage_metadata["total_tokens"] > 0
    assert (
        full.usage_metadata["input_tokens"] + full.usage_metadata["output_tokens"]
        == full.usage_metadata["total_tokens"]
    )
    assert "stop_reason" in full.response_metadata
    assert "stop_sequence" in full.response_metadata
    assert "model_name" in full.response_metadata