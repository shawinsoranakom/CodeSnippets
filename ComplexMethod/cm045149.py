async def test_create(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    model = "llama3.2"
    content_raw = "Hello world! This is a test response. Test response."

    async def _mock_chat(*args: Any, **kwargs: Any) -> ChatResponse:
        return ChatResponse(
            model=model,
            done=True,
            done_reason="stop",
            message=Message(
                role="assistant",
                content=content_raw,
            ),
            prompt_eval_count=10,
            eval_count=12,
        )

    monkeypatch.setattr(AsyncClient, "chat", _mock_chat)
    with caplog.at_level(logging.INFO):
        client = OllamaChatCompletionClient(model=model)
        create_result = await client.create(
            messages=[
                UserMessage(content="hi", source="user"),
            ],
        )
        assert "LLMCall" in caplog.text and content_raw in caplog.text
    assert isinstance(create_result.content, str)
    assert len(create_result.content) > 0
    assert create_result.finish_reason == "stop"
    assert create_result.usage is not None
    assert create_result.usage.prompt_tokens == 10
    assert create_result.usage.completion_tokens == 12
    assert create_result.content == content_raw