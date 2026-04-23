def test_agent_loop(model: str, output_version: str | None) -> None:
    """Test agent loop with tool calling and message passing."""

    @tool
    def get_weather(location: str) -> str:
        """Get the weather for a location."""
        return "It's sunny and 75 degrees."

    llm = ChatOllama(model=model, output_version=output_version, reasoning="low")
    llm_with_tools = llm.bind_tools([get_weather])

    input_message = HumanMessage("What is the weather in San Francisco, CA?")
    tool_call_message = llm_with_tools.invoke([input_message])
    assert isinstance(tool_call_message, AIMessage)

    tool_calls = tool_call_message.tool_calls
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["name"] == "get_weather"
    assert "location" in tool_call["args"]

    tool_message = get_weather.invoke(tool_call)
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.content
    assert isinstance(tool_message.content, str)
    assert "sunny" in tool_message.content.lower()

    resp_message = llm_with_tools.invoke(
        [
            input_message,
            tool_call_message,
            tool_message,
        ]
    )
    follow_up = HumanMessage("Explain why that might be using a reasoning step.")
    assert isinstance(resp_message, AIMessage)
    assert len(resp_message.content) > 0

    response = llm_with_tools.invoke(
        [input_message, tool_call_message, tool_message, resp_message, follow_up]
    )
    assert isinstance(resp_message, AIMessage)
    assert len(resp_message.content) > 0

    if output_version == "v1":
        content_blocks = response.content_blocks
        assert content_blocks is not None
        assert len(content_blocks) > 0
        assert any(block["type"] == "text" for block in content_blocks)
        assert any(block["type"] == "reasoning" for block in content_blocks)