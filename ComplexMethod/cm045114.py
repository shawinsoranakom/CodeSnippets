async def test_openai_chat_completion_client_create_stream_no_usage_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(AsyncCompletions, "create", _mock_create)
    client = OpenAIChatCompletionClient(model="gpt-4o", api_key="api_key")
    chunks: List[str | CreateResult] = []
    async for chunk in client.create_stream(
        messages=[UserMessage(content="Hello", source="user")],
        # include_usage not the default of the OPENAI APIis ,
        # it can be explicitly set
        # or just not declared which is the default
        # extra_create_args={"stream_options": {"include_usage": False}},
    ):
        chunks.append(chunk)
    assert chunks[0] == "Hello"
    assert chunks[1] == " Another Hello"
    assert chunks[2] == " Yet Another Hello"
    assert isinstance(chunks[-1], CreateResult)
    assert chunks[-1].content == "Hello Another Hello Yet Another Hello"
    assert chunks[-1].usage == RequestUsage(prompt_tokens=0, completion_tokens=0)