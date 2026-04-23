async def test_astream() -> None:
    """Test streaming tokens from Groq."""
    chat = ChatGroq(model=DEFAULT_MODEL_NAME, max_tokens=10)

    full: BaseMessageChunk | None = None
    chunks_with_token_counts = 0
    chunks_with_response_metadata = 0
    async for token in chat.astream("Welcome to the Groqetship!"):
        assert isinstance(token, AIMessageChunk)
        assert isinstance(token.content, str)
        full = token if full is None else full + token
        if token.usage_metadata is not None:
            chunks_with_token_counts += 1
        if token.response_metadata and not set(token.response_metadata.keys()).issubset(
            {"model_provider", "output_version"}
        ):
            chunks_with_response_metadata += 1
    if chunks_with_token_counts != 1 or chunks_with_response_metadata != 1:
        msg = (
            "Expected exactly one chunk with token counts or metadata. "
            "AIMessageChunk aggregation adds / appends these metadata. Check that "
            "this is behaving properly."
        )
        raise AssertionError(msg)
    assert isinstance(full, AIMessageChunk)
    assert full.usage_metadata is not None
    assert full.usage_metadata["input_tokens"] > 0
    assert full.usage_metadata["output_tokens"] > 0
    assert (
        full.usage_metadata["input_tokens"] + full.usage_metadata["output_tokens"]
        == full.usage_metadata["total_tokens"]
    )
    for expected_metadata in ["model_name", "system_fingerprint"]:
        assert full.response_metadata[expected_metadata]