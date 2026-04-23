def test_tool_runtime_name_based_injection() -> None:
    """Test that parameter named 'runtime' gets injected without type annotation."""
    injected_data: dict[str, Any] = {}

    @tool
    def name_based_tool(x: int, runtime: Any) -> str:
        """Tool with 'runtime' parameter without ToolRuntime type annotation."""
        # Even though type is Any, runtime should still be injected as ToolRuntime
        injected_data["is_tool_runtime"] = isinstance(runtime, ToolRuntime)
        injected_data["has_state"] = hasattr(runtime, "state")
        injected_data["has_tool_call_id"] = hasattr(runtime, "tool_call_id")
        if hasattr(runtime, "tool_call_id"):
            injected_data["tool_call_id"] = runtime.tool_call_id
        if hasattr(runtime, "state"):
            injected_data["state"] = runtime.state
        return f"Processed {x}"

    agent = create_agent(
        model=FakeToolCallingModel(
            tool_calls=[
                [{"args": {"x": 42}, "id": "name_call_123", "name": "name_based_tool"}],
                [],
            ]
        ),
        tools=[name_based_tool],
        system_prompt="You are a helpful assistant.",
    )

    result = agent.invoke({"messages": [HumanMessage("Test")]})

    # Verify tool executed
    assert len(result["messages"]) == 4
    tool_message = result["messages"][2]
    assert isinstance(tool_message, ToolMessage)
    assert tool_message.content == "Processed 42"

    # Verify runtime was injected based on parameter name
    assert injected_data["is_tool_runtime"] is True
    assert injected_data["has_state"] is True
    assert injected_data["has_tool_call_id"] is True
    assert injected_data["tool_call_id"] == "name_call_123"
    assert injected_data["state"] is not None
    assert "messages" in injected_data["state"]