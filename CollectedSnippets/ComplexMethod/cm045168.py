async def test_tool_choice_default_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that default behavior (no tool_choice specified) works like 'auto'"""

    def add(x: int, y: int) -> str:
        return str(x + y)

    add_tool = FunctionTool(add, description="Add two numbers")
    model = "llama3.2"

    # Capture the kwargs passed to chat
    chat_kwargs_captured: Dict[str, Any] = {}

    async def _mock_chat(*args: Any, **kwargs: Any) -> ChatResponse:
        nonlocal chat_kwargs_captured
        chat_kwargs_captured = kwargs
        return ChatResponse(
            model=model,
            done=True,
            done_reason="stop",
            message=Message(
                role="assistant",
                content="I'll use the add tool.",
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

    monkeypatch.setattr(AsyncClient, "chat", _mock_chat)

    client = OllamaChatCompletionClient(model=model)
    create_result = await client.create(
        messages=[UserMessage(content="What is 2 + 3?", source="user")],
        tools=[add_tool],
        # tool_choice not specified - should default to "auto"
    )

    # Verify that tools are passed to the API by default (auto behavior)
    assert "tools" in chat_kwargs_captured
    assert chat_kwargs_captured["tools"] is not None
    assert len(chat_kwargs_captured["tools"]) == 1

    # Verify the response
    assert isinstance(create_result.content, list)
    assert len(create_result.content) > 0
    assert isinstance(create_result.content[0], FunctionCall)
    assert create_result.content[0].name == add_tool.name