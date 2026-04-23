async def test_non_streaming_product_tool_call(
    client: openai.AsyncOpenAI, server_config: ServerConfig
):
    """Test tool call integer and boolean parameters in non-streaming mode."""

    response = await client.chat.completions.create(
        model=server_config["model_arg"],
        messages=PRODUCT_MESSAGES,
        tools=PRODUCT_TOOLS,
        tool_choice="auto",
        temperature=0.66,
    )

    assert response.choices
    choice = response.choices[0]
    message = choice.message

    assert choice.finish_reason == "tool_calls"
    assert message.tool_calls is not None

    tool_call = message.tool_calls[0]
    assert tool_call.type == "function"
    assert tool_call.function.name == "get_product_info"

    arguments = json.loads(tool_call.function.arguments)
    assert "product_id" in arguments
    assert "inserted" in arguments

    product_id = arguments.get("product_id")
    inserted = arguments.get("inserted")

    assert isinstance(product_id, int)
    assert product_id == 7355608
    assert isinstance(inserted, bool)
    assert inserted is True

    print("\n[Non-Streaming Product Test Passed]")
    print(f"Tool Call: {tool_call.function.name}")
    print(f"Arguments: {arguments}")