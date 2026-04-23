def test_custom_tool(output_version: Literal["responses/v1", "v1"]) -> None:
    @custom_tool
    def execute_code(code: str) -> str:
        """Execute python code."""
        return "27"

    llm = ChatOpenAI(model="gpt-5", output_version=output_version).bind_tools(
        [execute_code]
    )

    input_message = {"role": "user", "content": "Use the tool to evaluate 3^3."}
    tool_call_message = llm.invoke([input_message])
    assert isinstance(tool_call_message, AIMessage)
    assert len(tool_call_message.tool_calls) == 1
    tool_call = tool_call_message.tool_calls[0]
    tool_message = execute_code.invoke(tool_call)
    response = llm.invoke([input_message, tool_call_message, tool_message])
    assert isinstance(response, AIMessage)

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in llm.stream([input_message]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert len(full.tool_calls) == 1