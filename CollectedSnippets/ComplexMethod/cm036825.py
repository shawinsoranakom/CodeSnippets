async def test_streaming_product_tool_call(
    client: openai.AsyncOpenAI, server_config: ServerConfig
):
    """Test tool call integer and boolean parameters in streaming mode."""

    stream = await client.chat.completions.create(
        model=server_config["model_arg"],
        messages=PRODUCT_MESSAGES,
        tools=PRODUCT_TOOLS,
        tool_choice="auto",
        temperature=0.66,
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

    assert reconstructed_tool_call["name"] == "get_product_info"

    arguments = json.loads(reconstructed_tool_call["arguments"])
    assert "product_id" in arguments
    assert "inserted" in arguments

    # Handle type coercion for streaming test as well
    product_id = arguments.get("product_id")
    inserted = arguments.get("inserted")

    assert isinstance(product_id, int)
    assert product_id == 7355608
    assert isinstance(inserted, bool)
    assert inserted is True

    print("\n[Streaming Product Test Passed]")
    print(f"Reconstructed Tool Call: {reconstructed_tool_call['name']}")
    print(f"Reconstructed Arguments: {arguments}")