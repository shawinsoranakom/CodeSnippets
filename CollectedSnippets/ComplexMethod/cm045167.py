async def test_tool_choice_stream_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test tool_choice='none' with streaming"""

    def add(x: int, y: int) -> str:
        return str(x + y)

    add_tool = FunctionTool(add, description="Add two numbers")
    model = "llama3.2"
    content_raw = "I cannot use tools, so I'll calculate manually: 2 + 3 = 5"

    # Capture the kwargs passed to chat
    chat_kwargs_captured: Dict[str, Any] = {}

    async def _mock_chat(*args: Any, **kwargs: Any) -> AsyncGenerator[ChatResponse, None]:
        nonlocal chat_kwargs_captured
        chat_kwargs_captured = kwargs
        assert "stream" in kwargs
        assert kwargs["stream"] is True

        async def _mock_stream() -> AsyncGenerator[ChatResponse, None]:
            chunks = [content_raw[i : i + 10] for i in range(0, len(content_raw), 10)]
            # Simulate streaming by yielding chunks of the response
            for chunk in chunks[:-1]:
                yield ChatResponse(
                    model=model,
                    done=False,
                    message=Message(
                        role="assistant",
                        content=chunk,
                    ),
                )
            yield ChatResponse(
                model=model,
                done=True,
                done_reason="stop",
                message=Message(
                    role="assistant",
                    content=chunks[-1],
                ),
                prompt_eval_count=10,
                eval_count=12,
            )

        return _mock_stream()

    monkeypatch.setattr(AsyncClient, "chat", _mock_chat)

    client = OllamaChatCompletionClient(model=model)
    stream = client.create_stream(
        messages=[UserMessage(content="What is 2 + 3?", source="user")],
        tools=[add_tool],
        tool_choice="none",
    )

    chunks: List[str | CreateResult] = []
    async for chunk in stream:
        chunks.append(chunk)

    # Verify that no tools are passed to the API when tool_choice is none
    assert "tools" in chat_kwargs_captured
    assert chat_kwargs_captured["tools"] is None

    # Verify the final result is text content
    assert len(chunks) > 0
    assert isinstance(chunks[-1], CreateResult)
    assert isinstance(chunks[-1].content, str)
    assert chunks[-1].content == content_raw
    assert chunks[-1].finish_reason == "stop"