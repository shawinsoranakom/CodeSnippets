async def test_tool_choice_stream_auto(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test tool_choice='auto' with streaming"""

    def add(x: int, y: int) -> str:
        return str(x + y)

    add_tool = FunctionTool(add, description="Add two numbers")
    model = "llama3.2"
    content_raw = "I'll use the add tool."

    # Capture the kwargs passed to chat
    chat_kwargs_captured: Dict[str, Any] = {}

    async def _mock_chat(*args: Any, **kwargs: Any) -> AsyncGenerator[ChatResponse, None]:
        nonlocal chat_kwargs_captured
        chat_kwargs_captured = kwargs
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
                done_reason="tool_calls",
                message=Message(
                    content=chunks[-1],
                    role="assistant",
                    tool_calls=[
                        Message.ToolCall(
                            function=Message.ToolCall.Function(
                                name=add_tool.name,
                                arguments={"x": 2, "y": 3},
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
        messages=[UserMessage(content="What is 2 + 3?", source="user")],
        tools=[add_tool],
        tool_choice="auto",
    )

    chunks: List[str | CreateResult] = []
    async for chunk in stream:
        chunks.append(chunk)

    # Verify that tools are passed to the API when tool_choice is auto
    assert "tools" in chat_kwargs_captured
    assert chat_kwargs_captured["tools"] is not None
    assert len(chat_kwargs_captured["tools"]) == 1

    # Verify the final result
    assert len(chunks) > 0
    assert isinstance(chunks[-1], CreateResult)
    assert isinstance(chunks[-1].content, list)
    assert len(chunks[-1].content) > 0
    assert isinstance(chunks[-1].content[0], FunctionCall)
    assert chunks[-1].content[0].name == add_tool.name
    assert chunks[-1].finish_reason == "function_calls"