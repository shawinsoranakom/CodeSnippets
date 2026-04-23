async def test_streaming_tool_call(
    client: openai.AsyncOpenAI, server_config: ServerConfig
):
    """Test tool call in streaming mode."""

    stream = await client.chat.completions.create(
        model=server_config["model_arg"],
        messages=MESSAGES,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0.0,
        stream=True,
    )

    tool_call_chunks = {}
    async for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        if not delta or not delta.tool_calls:
            continue

        for tool_chunk in delta.tool_calls:
            index = tool_chunk.index
            if index not in tool_call_chunks:
                tool_call_chunks[index] = {"name": "", "arguments": ""}

            if tool_chunk.function.name:
                tool_call_chunks[index]["name"] += tool_chunk.function.name
            if tool_chunk.function.arguments:
                tool_call_chunks[index]["arguments"] += tool_chunk.function.arguments

    assert len(tool_call_chunks) == 1
    reconstructed_tool_call = tool_call_chunks[0]

    assert reconstructed_tool_call["name"] == "get_current_weather"

    arguments = json.loads(reconstructed_tool_call["arguments"])
    assert "location" in arguments
    assert "Boston" in arguments["location"]
    print("\n[Streaming Test Passed]")
    print(f"Reconstructed Tool Call: {reconstructed_tool_call['name']}")
    print(f"Reconstructed Arguments: {arguments}")