async def test_ollama_create_tools(model: str, ollama_client: OllamaChatCompletionClient) -> None:
    def add(x: int, y: int) -> str:
        return str(x + y)

    add_tool = FunctionTool(add, description="Add two numbers")

    create_result = await ollama_client.create(
        messages=[
            UserMessage(
                content="What is 2 + 2? Use the add tool.",
                source="user",
            ),
        ],
        tools=[add_tool],
    )
    assert isinstance(create_result.content, list)
    assert len(create_result.content) > 0
    assert isinstance(create_result.content[0], FunctionCall)
    assert create_result.content[0].name == add_tool.name
    assert create_result.content[0].arguments == json.dumps({"x": 2, "y": 2})
    assert create_result.finish_reason == "function_calls"

    execution_result = FunctionExecutionResult(
        content="4",
        name=add_tool.name,
        call_id=create_result.content[0].id,
        is_error=False,
    )
    create_result = await ollama_client.create(
        messages=[
            UserMessage(
                content="What is 2 + 2? Use the add tool.",
                source="user",
            ),
            AssistantMessage(
                content=create_result.content,
                source="assistant",
            ),
            FunctionExecutionResultMessage(
                content=[execution_result],
            ),
        ],
    )
    assert isinstance(create_result.content, str)
    assert len(create_result.content) > 0
    assert create_result.finish_reason == "stop"