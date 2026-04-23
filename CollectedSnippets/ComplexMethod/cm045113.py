async def test_openai_chat_completion_client_create_stream_with_usage(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(AsyncCompletions, "create", _mock_create)
    client = OpenAIChatCompletionClient(model="gpt-4o", api_key="api_key")
    chunks: List[str | CreateResult] = []
    # Check that include_usage works when set via create_args
    with caplog.at_level(logging.INFO):
        async for chunk in client.create_stream(
            messages=[UserMessage(content="Hello", source="user")],
            # include_usage not the default of the OPENAI API and must be explicitly set
            extra_create_args={"stream_options": {"include_usage": True}},
        ):
            chunks.append(chunk)

        assert "LLMStreamStart" in caplog.text
        assert "LLMStreamEnd" in caplog.text

        assert chunks[0] == "Hello"
        assert chunks[1] == " Another Hello"
        assert chunks[2] == " Yet Another Hello"
        assert isinstance(chunks[-1], CreateResult)
        assert isinstance(chunks[-1].content, str)
        assert chunks[-1].content == "Hello Another Hello Yet Another Hello"
        assert chunks[-1].content in caplog.text
        assert chunks[-1].usage == RequestUsage(prompt_tokens=3, completion_tokens=3)

    chunks = []
    # Check that include_usage works when set via include_usage flag
    with caplog.at_level(logging.INFO):
        async for chunk in client.create_stream(
            messages=[UserMessage(content="Hello", source="user")],
            include_usage=True,
        ):
            chunks.append(chunk)

        assert "LLMStreamStart" in caplog.text
        assert "LLMStreamEnd" in caplog.text

        assert chunks[0] == "Hello"
        assert chunks[1] == " Another Hello"
        assert chunks[2] == " Yet Another Hello"
        assert isinstance(chunks[-1], CreateResult)
        assert isinstance(chunks[-1].content, str)
        assert chunks[-1].content == "Hello Another Hello Yet Another Hello"
        assert chunks[-1].content in caplog.text
        assert chunks[-1].usage == RequestUsage(prompt_tokens=3, completion_tokens=3)

    chunks = []
    # Check that setting both flags to different values raises an exception

    with pytest.raises(ValueError):
        async for chunk in client.create_stream(
            messages=[UserMessage(content="Hello", source="user")],
            extra_create_args={"stream_options": {"include_usage": False}},
            include_usage=True,
        ):
            chunks.append(chunk)