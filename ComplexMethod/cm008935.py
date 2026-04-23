def test_tool_invocation_error_excludes_injected_state() -> None:
    """Test that tool invocation errors only include LLM-controllable arguments.

    When a tool has InjectedState parameters and the LLM makes an incorrect
    invocation (e.g., missing required arguments), the error message should only
    contain the arguments from the tool call that the LLM controls. This ensures
    the LLM receives relevant context to correct its mistakes, without being
    distracted by system-injected parameters it has no control over.
    This test uses create_agent to ensure the behavior works in a full agent context.
    """

    # Define a custom state schema with injected data
    class TestState(AgentState[Any]):
        secret_data: str  # Example of state data not controlled by LLM

    @dec_tool
    def tool_with_injected_state(
        some_val: int,
        state: Annotated[TestState, InjectedState],
    ) -> str:
        """Tool that uses injected state."""
        return f"some_val: {some_val}"

    # Create a fake model that makes an incorrect tool call (missing 'some_val')
    # Then returns no tool calls on the second iteration to end the loop
    model = FakeToolCallingModel(
        tool_calls=[
            [
                {
                    "name": "tool_with_injected_state",
                    "args": {"wrong_arg": "value"},  # Missing required 'some_val'
                    "id": "call_1",
                }
            ],
            [],  # No tool calls on second iteration to end the loop
        ]
    )

    # Create an agent with the tool and custom state schema
    agent = create_agent(
        model=model,
        tools=[tool_with_injected_state],
        state_schema=TestState,
    )

    # Invoke the agent with injected state data
    result = agent.invoke(
        {
            "messages": [HumanMessage("Test message")],
            "secret_data": "sensitive_secret_123",
        }
    )

    # Find the tool error message
    tool_messages = [m for m in result["messages"] if m.type == "tool"]
    assert len(tool_messages) == 1
    tool_message = tool_messages[0]
    assert tool_message.status == "error"

    # The error message should contain only the LLM-provided args (wrong_arg)
    # and NOT the system-injected state (secret_data)
    assert "{'wrong_arg': 'value'}" in tool_message.content
    assert "secret_data" not in tool_message.content
    assert "sensitive_secret_123" not in tool_message.content