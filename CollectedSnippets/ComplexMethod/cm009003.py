def test_tools_to_model_edge_with_structured_and_regular_tool_calls() -> None:
    """Test tools to model edge with structured and regular tool calls.

    Test that when there are both structured and regular tool calls, we execute regular
    and jump to END.
    """

    class WeatherResponse(BaseModel):
        """Weather response."""

        temperature: float = Field(description="Temperature in fahrenheit")
        condition: str = Field(description="Weather condition")

    @tool
    def regular_tool(query: str) -> str:
        """A regular tool that returns a string."""
        return f"Regular tool result for: {query}"

    # Create a fake model that returns both structured and regular tool calls
    class FakeModelWithBothToolCalls(FakeToolCallingModel):
        def __init__(self) -> None:
            super().__init__()
            self.tool_calls = [
                [
                    ToolCall(
                        name="WeatherResponse",
                        args={"temperature": 72.0, "condition": "sunny"},
                        id="structured_call_1",
                    ),
                    ToolCall(
                        name="regular_tool", args={"query": "test query"}, id="regular_call_1"
                    ),
                ]
            ]

    # Create agent with both structured output and regular tools
    agent = create_agent(
        model=FakeModelWithBothToolCalls(),
        tools=[regular_tool],
        response_format=ToolStrategy(schema=WeatherResponse),
    )

    # Invoke the agent (already compiled)
    result = agent.invoke(
        {"messages": [HumanMessage("What's the weather and help me with a query?")]}
    )

    # Verify that we have the expected messages:
    # 1. Human message
    # 2. AI message with both tool calls
    # 3. Tool message from structured tool call
    # 4. Tool message from regular tool call

    messages = result["messages"]
    assert len(messages) >= 4

    # Check that we have the AI message with both tool calls
    ai_message = messages[1]
    assert isinstance(ai_message, AIMessage)
    assert len(ai_message.tool_calls) == 2

    # Check that we have a tool message from the regular tool
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    assert len(tool_messages) >= 1

    # The regular tool should have been executed
    regular_tool_message = next((m for m in tool_messages if m.name == "regular_tool"), None)
    assert regular_tool_message is not None
    assert "Regular tool result for: test query" in regular_tool_message.content

    # Verify that the structured response is available in the result
    assert "structured_response" in result
    assert result["structured_response"] is not None
    assert hasattr(result["structured_response"], "temperature")
    assert result["structured_response"].temperature == 72.0
    assert result["structured_response"].condition == "sunny"