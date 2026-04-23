async def test_mcp_tool_multi_turn(client: OpenAI, model_name: str, server):
    """MCP tools work across multiple turns via previous_response_id."""
    tools = [{"type": "mcp", "server_label": "code_interpreter"}]
    instructions = (
        "You must use the Python tool to execute code. Never simulate execution."
    )

    # First turn
    response1 = await retry_for_tool_call(
        client,
        model=model_name,
        expected_tool_type="mcp_call",
        input="Calculate 1234 * 4567 using python tool and print the result.",
        tools=tools,
        temperature=0.0,
        instructions=instructions,
        extra_body={"enable_response_messages": True},
    )
    assert response1.status == "completed"

    # Verify MCP call in output_messages
    tool_call_found = any(
        (msg.get("recipient") or "").startswith("python")
        for msg in response1.output_messages
    )
    parsed_output_messages = [
        Message.from_dict(msg) for msg in response1.output_messages
    ]
    tool_response_found = any(
        (msg.author.role == "tool" and (msg.author.name or "").startswith("python"))
        for msg in parsed_output_messages
    )
    assert tool_call_found, "MCP tool call not found in output_messages"
    assert tool_response_found, "MCP tool response not found in output_messages"

    # No developer messages expected for elevated tools
    developer_msgs = [
        msg
        for msg in (Message.from_dict(raw) for raw in response1.input_messages)
        if msg.author.role == "developer"
    ]
    assert len(developer_msgs) == 0, "No developer message expected for elevated tools"

    # Second turn
    response2 = await client.responses.create(
        model=model_name,
        input="Now divide that result by 2.",
        tools=tools,
        temperature=0.0,
        instructions=instructions,
        previous_response_id=response1.id,
        extra_body={"enable_response_messages": True},
    )
    assert response2.status == "completed"