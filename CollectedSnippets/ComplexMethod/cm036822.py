async def test_non_streaming_tool_call(
    client: openai.AsyncOpenAI, server_config: ServerConfig
):
    """Test tool call in non-streaming mode."""

    response = await client.chat.completions.create(
        model=server_config["model_arg"],
        messages=MESSAGES,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.0,
    )

    assert response.choices
    choice = response.choices[0]
    message = choice.message

    assert choice.finish_reason == "tool_calls"
    assert message.tool_calls is not None

    tool_call = message.tool_calls[0]
    assert tool_call.type == "function"
    assert tool_call.function.name == "get_current_weather"

    arguments = json.loads(tool_call.function.arguments)
    assert "location" in arguments
    assert "Boston" in arguments["location"]
    print("\n[Non-Streaming Test Passed]")
    print(f"Tool Call: {tool_call.function.name}")
    print(f"Arguments: {arguments}")