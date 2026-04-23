async def test_tool_choice_specific_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test tool_choice with a specific tool - only that tool should be passed to API"""

    def add(x: int, y: int) -> str:
        return str(x + y)

    def multiply(x: int, y: int) -> str:
        return str(x * y)

    add_tool = FunctionTool(add, description="Add two numbers")
    multiply_tool = FunctionTool(multiply, description="Multiply two numbers")
    model = "llama3.2"

    # Capture the kwargs passed to chat
    chat_kwargs_captured: Dict[str, Any] = {}

    async def _mock_chat(*args: Any, **kwargs: Any) -> ChatResponse:
        nonlocal chat_kwargs_captured
        chat_kwargs_captured = kwargs
        return ChatResponse(
            model=model,
            done=True,
            done_reason="tool_calls",
            message=Message(
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

    monkeypatch.setattr(AsyncClient, "chat", _mock_chat)

    client = OllamaChatCompletionClient(model=model)
    create_result = await client.create(
        messages=[UserMessage(content="What is 2 + 3?", source="user")],
        tools=[add_tool, multiply_tool],  # Multiple tools available
        tool_choice=add_tool,  # But force specific tool
    )

    # Verify that only the specified tool is passed to the API
    assert "tools" in chat_kwargs_captured
    assert chat_kwargs_captured["tools"] is not None
    assert len(chat_kwargs_captured["tools"]) == 1
    assert chat_kwargs_captured["tools"][0]["function"]["name"] == add_tool.name

    # Verify the response contains function calls
    assert isinstance(create_result.content, list)
    assert len(create_result.content) > 0
    assert isinstance(create_result.content[0], FunctionCall)
    assert create_result.content[0].name == add_tool.name
    assert create_result.finish_reason == "function_calls"