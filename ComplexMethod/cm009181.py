async def test_openai_astream(mock_openai_completion: list) -> None:
    llm_name = "gpt-4o"
    llm = ChatOpenAI(model=llm_name)
    assert llm.stream_usage
    mock_client = AsyncMock()

    async def mock_create(*args: Any, **kwargs: Any) -> MockAsyncContextManager:
        return MockAsyncContextManager(mock_openai_completion)

    mock_client.create = mock_create
    usage_chunk = mock_openai_completion[-1]
    usage_metadata: UsageMetadata | None = None
    with patch.object(llm, "async_client", mock_client):
        async for chunk in llm.astream("你的名字叫什么？只回答名字"):
            assert isinstance(chunk, AIMessageChunk)
            if chunk.usage_metadata is not None:
                usage_metadata = chunk.usage_metadata

    assert usage_metadata is not None

    assert usage_metadata["input_tokens"] == usage_chunk["usage"]["prompt_tokens"]
    assert usage_metadata["output_tokens"] == usage_chunk["usage"]["completion_tokens"]
    assert usage_metadata["total_tokens"] == usage_chunk["usage"]["total_tokens"]