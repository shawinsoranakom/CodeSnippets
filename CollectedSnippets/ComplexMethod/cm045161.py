async def test_create_tools_with_thought(monkeypatch: pytest.MonkeyPatch) -> None:
    def add(x: int, y: int) -> str:
        return str(x + y)

    add_tool = FunctionTool(add, description="Add two numbers")
    model = "llama3.2"
    thought_content = "I'll use the add tool to calculate 2 + 2."

    async def _mock_chat(*args: Any, **kwargs: Any) -> ChatResponse:
        return ChatResponse(
            model=model,
            done=True,
            done_reason="tool_calls",
            message=Message(
                role="assistant",
                content=thought_content,
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

    monkeypatch.setattr(AsyncClient, "chat", _mock_chat)
    client = OllamaChatCompletionClient(model=model)

    create_result = await client.create(
        messages=[
            UserMessage(content="What is 2 + 2?", source="user"),
        ],
        tools=[add_tool],
    )

    assert isinstance(create_result.content, list)
    assert len(create_result.content) > 0
    assert isinstance(create_result.content[0], FunctionCall)
    assert create_result.content[0].name == add_tool.name
    assert create_result.content[0].arguments == json.dumps({"x": 2, "y": 2})

    assert create_result.thought == thought_content

    assert create_result.finish_reason == "function_calls"
    assert create_result.usage is not None
    assert create_result.usage.prompt_tokens == 10
    assert create_result.usage.completion_tokens == 12