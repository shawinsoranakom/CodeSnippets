def test_injected_state_in_middleware_agent() -> None:
    """Test that custom state is properly injected into tools when using middleware."""
    result = agent.invoke(
        {
            "custom_state": "I love pizza",
            "messages": [HumanMessage("Call the test state tool")],
        }
    )

    messages = result["messages"]
    assert len(messages) == 4  # Human message, AI message with tool call, tool message, AI message

    # Find the tool message
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    assert len(tool_messages) == 1

    tool_message = tool_messages[0]
    assert tool_message.name == "test_state_tool"
    assert "success" in tool_message.content
    assert tool_message.tool_call_id == "test_call_1"