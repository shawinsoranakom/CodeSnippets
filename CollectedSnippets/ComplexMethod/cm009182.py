def test_openai_stream(mock_openai_completion: list) -> None:
    llm_name = "gpt-4o"
    llm = ChatOpenAI(model=llm_name)
    assert llm.stream_usage
    mock_client = MagicMock()

    call_kwargs = []

    def mock_create(*args: Any, **kwargs: Any) -> MockSyncContextManager:
        call_kwargs.append(kwargs)
        return MockSyncContextManager(mock_openai_completion)

    mock_client.create = mock_create
    usage_chunk = mock_openai_completion[-1]
    usage_metadata: UsageMetadata | None = None
    with patch.object(llm, "client", mock_client):
        for chunk in llm.stream("你的名字叫什么？只回答名字"):
            assert isinstance(chunk, AIMessageChunk)
            if chunk.usage_metadata is not None:
                usage_metadata = chunk.usage_metadata

    assert call_kwargs[-1]["stream_options"] == {"include_usage": True}
    assert usage_metadata is not None
    assert usage_metadata["input_tokens"] == usage_chunk["usage"]["prompt_tokens"]
    assert usage_metadata["output_tokens"] == usage_chunk["usage"]["completion_tokens"]
    assert usage_metadata["total_tokens"] == usage_chunk["usage"]["total_tokens"]

    # Verify no streaming outside of default base URL or clients
    for param, value in {
        "stream_usage": False,
        "openai_proxy": "http://localhost:7890",
        "openai_api_base": "https://example.com/v1",
        "base_url": "https://example.com/v1",
        "client": mock_client,
        "root_client": mock_client,
        "async_client": mock_client,
        "root_async_client": mock_client,
        "http_client": httpx.Client(),
        "http_async_client": httpx.AsyncClient(),
    }.items():
        llm = ChatOpenAI(model=llm_name, **{param: value})  # type: ignore[arg-type]
        assert not llm.stream_usage
        with patch.object(llm, "client", mock_client):
            _ = list(llm.stream("..."))
        assert "stream_options" not in call_kwargs[-1]