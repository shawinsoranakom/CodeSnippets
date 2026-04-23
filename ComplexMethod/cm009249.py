def test_programmatic_tool_use_streaming(output_version: str) -> None:
    @tool(extras={"allowed_callers": ["code_execution_20250825"]})
    def get_weather(location: str) -> str:
        """Get the weather at a location."""
        return "It's sunny."

    tools: list = [
        {"type": "code_execution_20250825", "name": "code_execution"},
        get_weather,
    ]

    model = ChatAnthropic(
        model="claude-sonnet-4-5",
        betas=["advanced-tool-use-2025-11-20"],
        reuse_last_container=True,
        streaming=True,
        output_version=output_version,
    )

    agent = create_agent(model, tools=tools)  # type: ignore[var-annotated]

    input_query = {
        "role": "user",
        "content": "What's the weather in Boston?",
    }

    result = agent.invoke({"messages": [input_query]})
    assert len(result["messages"]) == 4
    tool_call_message = result["messages"][1]
    response_message = result["messages"][-1]

    if output_version == "v0":
        server_tool_use_block = next(
            block
            for block in tool_call_message.content
            if block["type"] == "server_tool_use"
        )
        assert server_tool_use_block

        tool_use_block = next(
            block for block in tool_call_message.content if block["type"] == "tool_use"
        )
        assert "caller" in tool_use_block

        code_execution_result = next(
            block
            for block in response_message.content
            if block["type"] == "code_execution_tool_result"
        )
        assert code_execution_result["content"]["return_code"] == 0
    else:
        server_tool_call_block = next(
            block
            for block in tool_call_message.content
            if block["type"] == "server_tool_call"
        )
        assert server_tool_call_block

        tool_call_block = next(
            block for block in tool_call_message.content if block["type"] == "tool_call"
        )
        assert "caller" in tool_call_block["extras"]

        server_tool_result = next(
            block
            for block in response_message.content
            if block["type"] == "server_tool_result"
        )
        assert server_tool_result["output"]["return_code"] == 0