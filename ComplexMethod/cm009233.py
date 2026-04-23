async def test_async_tool_use() -> None:
    llm = ChatAnthropic(
        model=MODEL_NAME,  # type: ignore[call-arg]
    )

    llm_with_tools = llm.bind_tools(
        [
            {
                "name": "get_weather",
                "description": "Get weather report for a city",
                "input_schema": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                },
            },
        ],
    )
    response = await llm_with_tools.ainvoke("what's the weather in san francisco, ca")
    assert isinstance(response, AIMessage)
    assert isinstance(response.content, list)
    assert isinstance(response.tool_calls, list)
    assert len(response.tool_calls) == 1
    tool_call = response.tool_calls[0]
    assert tool_call["name"] == "get_weather"
    assert isinstance(tool_call["args"], dict)
    assert "location" in tool_call["args"]

    # Test streaming
    first = True
    chunks: list[BaseMessage | BaseMessageChunk] = []
    async for chunk in llm_with_tools.astream(
        "what's the weather in san francisco, ca",
    ):
        chunks = [*chunks, chunk]
        if first:
            gathered = chunk
            first = False
        else:
            gathered = gathered + chunk  # type: ignore[assignment]
    assert len(chunks) > 1
    assert isinstance(gathered, AIMessageChunk)
    assert isinstance(gathered.tool_call_chunks, list)
    assert len(gathered.tool_call_chunks) == 1
    tool_call_chunk = gathered.tool_call_chunks[0]
    assert tool_call_chunk["name"] == "get_weather"
    assert isinstance(tool_call_chunk["args"], str)
    assert "location" in json.loads(tool_call_chunk["args"])