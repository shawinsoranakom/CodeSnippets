async def test_ollama_create_structured_output_with_tools(
    model: str, ollama_client: OllamaChatCompletionClient
) -> None:
    class ResponseType(BaseModel):
        calculation: str
        result: str

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
        json_output=ResponseType,
    )
    assert isinstance(create_result.content, list)
    assert len(create_result.content) > 0
    assert isinstance(create_result.content[0], FunctionCall)
    assert create_result.content[0].name == add_tool.name
    assert create_result.finish_reason == "function_calls"
    assert create_result.thought is not None
    assert ResponseType.model_validate_json(create_result.thought)