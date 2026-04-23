async def test_create_stream_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    def add(x: int, y: int) -> str:
        return str(x + y)

    add_tool = FunctionTool(add, description="Add two numbers")
    model = "llama3.2"
    content_raw = "Hello world! This is a test response. Test response."

    async def _mock_chat(*args: Any, **kwargs: Any) -> AsyncGenerator[ChatResponse, None]:
        assert "stream" in kwargs
        assert kwargs["stream"] is True

        async def _mock_stream() -> AsyncGenerator[ChatResponse, None]:
            chunks = [content_raw[i : i + 5] for i in range(0, len(content_raw), 5)]
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
                    content=chunks[-1],
                    role="assistant",
                    tool_calls=[
                        Message.ToolCall(
                            function=Message.ToolCall.Function(
                                name=add_tool.name,
                                arguments={"x": 2, "y": 2},
                            ),
                        ),
                    ],
                ),
                prompt_eval_count=10,
                eval_count=12,
            )

        return _mock_stream()

    monkeypatch.setattr(AsyncClient, "chat", _mock_chat)
    client = OllamaChatCompletionClient(model=model)
    stream = client.create_stream(
        messages=[
            UserMessage(content="hi", source="user"),
        ],
        tools=[add_tool],
    )
    chunks: List[str | CreateResult] = []
    async for chunk in stream:
        chunks.append(chunk)
    assert len(chunks) > 0
    assert isinstance(chunks[-1], CreateResult)
    assert isinstance(chunks[-1].content, list)
    assert len(chunks[-1].content) > 0
    assert isinstance(chunks[-1].content[0], FunctionCall)
    assert chunks[-1].content[0].name == add_tool.name
    assert chunks[-1].content[0].arguments == json.dumps({"x": 2, "y": 2})
    assert chunks[-1].finish_reason == "stop"
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.prompt_tokens == 10
    assert chunks[-1].usage.completion_tokens == 12