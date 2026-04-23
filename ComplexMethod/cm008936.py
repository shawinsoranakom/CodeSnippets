async def test_tool_invocation_error_excludes_injected_state_async() -> None:
    """Test that async tool invocation errors only include LLM-controllable arguments.

    This test verifies that the async execution path (_execute_tool_async and _arun_one)
    properly filters validation errors to exclude system-injected arguments, ensuring
    the LLM receives only relevant context for correction.
    """

    # Define a custom state schema
    class TestState(AgentState[Any]):
        internal_data: str

    @dec_tool
    async def async_tool_with_injected_state(
        query: str,
        max_results: int,
        state: Annotated[TestState, InjectedState],
    ) -> str:
        """Async tool that uses injected state."""
        return f"query: {query}, max_results: {max_results}"

    # Create a fake model that makes an incorrect tool call
    # - query has wrong type (int instead of str)
    # - max_results is missing
    model = FakeToolCallingModel(
        tool_calls=[
            [
                {
                    "name": "async_tool_with_injected_state",
                    "args": {"query": 999},  # Wrong type, missing max_results
                    "id": "call_async_1",
                }
            ],
            [],  # End the loop
        ]
    )

    # Create an agent with the async tool
    agent = create_agent(
        model=model,
        tools=[async_tool_with_injected_state],
        state_schema=TestState,
    )

    # Invoke with state data
    result = await agent.ainvoke(
        {
            "messages": [HumanMessage("Test async")],
            "internal_data": "secret_internal_value_xyz",
        }
    )

    # Find the tool error message
    tool_messages = [m for m in result["messages"] if m.type == "tool"]
    assert len(tool_messages) == 1
    tool_message = tool_messages[0]
    assert tool_message.status == "error"

    # Verify error mentions LLM-controlled parameters only
    content = tool_message.content
    assert "query" in content.lower(), "Error should mention 'query' (LLM-controlled)"
    assert "max_results" in content.lower(), "Error should mention 'max_results' (LLM-controlled)"

    # Verify system-injected state does not appear in the validation errors
    # This keeps the error focused on what the LLM can actually fix
    assert "internal_data" not in content, (
        "Error should NOT mention 'internal_data' (system-injected field)"
    )
    assert "secret_internal_value" not in content, (
        "Error should NOT contain system-injected state values"
    )

    # Verify only LLM-controlled parameters are in the error list
    # Should see "query" and "max_results" errors, but not "state"
    lines = content.split("\n")
    error_lines = [line.strip() for line in lines if line.strip()]
    # Find lines that look like field names (single words at start of line)
    field_errors = [
        line
        for line in error_lines
        if line
        and not line.startswith("input")
        and not line.startswith("field")
        and not line.startswith("error")
        and not line.startswith("please")
        and len(line.split()) <= 2
    ]
    # Verify system-injected 'state' is not in the field error list
    assert not any(field.lower() == "state" for field in field_errors), (
        "The field 'state' (system-injected) should not appear in validation errors"
    )