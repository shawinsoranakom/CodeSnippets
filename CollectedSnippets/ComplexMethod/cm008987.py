def test_structured_output_retry_preserves_messages() -> None:
    """Test structured output retry preserves error feedback in messages."""
    # First attempt invalid, second succeeds
    tool_calls = [
        [
            {
                "name": "WeatherReport",
                "id": "1",
                "args": {"temperature": "invalid", "conditions": "rainy"},
            }
        ],
        [
            {
                "name": "WeatherReport",
                "id": "2",
                "args": {"temperature": 75.0, "conditions": "rainy"},
            }
        ],
    ]

    model = FakeToolCallingModel(tool_calls=tool_calls)
    retry_middleware = StructuredOutputRetryMiddleware(max_retries=1)

    agent = create_agent(
        model=model,
        tools=[get_weather],
        middleware=[retry_middleware],
        response_format=ToolStrategy(schema=WeatherReport, handle_errors=False),
        checkpointer=InMemorySaver(),
    )

    result = agent.invoke(
        {"messages": [HumanMessage("What's the weather in Seattle?")]},
        {"configurable": {"thread_id": "test"}},
    )

    # Verify structured response is correct
    assert "structured_response" in result
    structured = result["structured_response"]
    assert structured.temperature == 75.0
    assert structured.conditions == "rainy"

    # Verify messages include the retry feedback
    messages = result["messages"]
    human_messages = [m for m in messages if isinstance(m, HumanMessage)]

    # Should have at least 2 human messages: initial + retry feedback
    assert len(human_messages) >= 2

    # The retry feedback message should contain error information
    retry_message = human_messages[-1]
    assert "Error:" in retry_message.content
    assert "Please try again" in retry_message.content