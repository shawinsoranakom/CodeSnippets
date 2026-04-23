def test_tool_search_streaming(output_version: str) -> None:
    @tool(extras={"defer_loading": True})
    def get_weather(location: str) -> str:
        """Get the current weather for a location."""
        return f"The weather in {location} is sunny and 72°F"

    @tool(extras={"defer_loading": True})
    def get_recipe(query: str) -> None:
        """Get a recipe for chicken soup."""

    model = ChatOpenAI(
        model="gpt-5.4",
        use_responses_api=True,
        streaming=True,
        output_version=output_version,
    )

    agent = create_agent(
        model=model,
        tools=[get_weather, get_recipe, {"type": "tool_search"}],
    )
    input_message = {"role": "user", "content": "What's the weather in San Francisco?"}
    result = agent.invoke({"messages": [input_message]})
    assert len(result["messages"]) == 4
    tool_call_message = result["messages"][1]
    assert isinstance(tool_call_message, AIMessage)
    assert tool_call_message.tool_calls
    if output_version == "v1":
        assert [block["type"] for block in tool_call_message.content] == [  # type: ignore[index]
            "server_tool_call",
            "server_tool_result",
            "tool_call",
        ]
    else:
        assert [block["type"] for block in tool_call_message.content] == [  # type: ignore[index]
            "tool_search_call",
            "tool_search_output",
            "function_call",
        ]

    assert isinstance(result["messages"][2], ToolMessage)

    assert result["messages"][3].text