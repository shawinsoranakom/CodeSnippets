async def test_ollama_create_stream_tools(model: str, ollama_client: OllamaChatCompletionClient) -> None:
    def add(x: int, y: int) -> str:
        return str(x + y)

    add_tool = FunctionTool(add, description="Add two numbers")

    stream = ollama_client.create_stream(
        messages=[
            UserMessage(
                content="What is 2 + 2? Use the add tool.",
                source="user",
            ),
        ],
        tools=[add_tool],
    )
    chunks: List[str | CreateResult] = []
    async for chunk in stream:
        chunks.append(chunk)
    assert len(chunks) > 0
    assert isinstance(chunks[-1], CreateResult)
    create_result = chunks[-1]
    assert isinstance(create_result.content, list)
    assert len(create_result.content) > 0
    assert isinstance(create_result.content[0], FunctionCall)
    assert create_result.content[0].name == add_tool.name
    assert create_result.content[0].arguments == json.dumps({"x": 2, "y": 2})
    assert create_result.finish_reason == "stop"
    assert create_result.usage is not None
    assert create_result.usage.prompt_tokens == 10
    assert create_result.usage.completion_tokens == 12