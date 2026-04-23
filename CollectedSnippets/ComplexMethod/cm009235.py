def test_tool_use() -> None:
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",  # type: ignore[call-arg]
        temperature=0,
    )
    tool_definition = {
        "name": "get_weather",
        "description": "Get weather report for a city",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
        },
    }
    llm_with_tools = llm.bind_tools([tool_definition])
    query = "how are you? what's the weather in san francisco, ca"
    response = llm_with_tools.invoke(query)
    assert isinstance(response, AIMessage)
    assert isinstance(response.content, list)
    assert isinstance(response.tool_calls, list)
    assert len(response.tool_calls) == 1
    tool_call = response.tool_calls[0]
    assert tool_call["name"] == "get_weather"
    assert isinstance(tool_call["args"], dict)
    assert "location" in tool_call["args"]

    content_blocks = response.content_blocks
    assert len(content_blocks) == 2
    assert content_blocks[0]["type"] == "text"
    assert content_blocks[0]["text"]
    assert content_blocks[1]["type"] == "tool_call"
    assert content_blocks[1]["name"] == "get_weather"
    assert content_blocks[1]["args"] == tool_call["args"]

    # Test streaming
    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")  # type: ignore[call-arg]
    llm_with_tools = llm.bind_tools([tool_definition])
    first = True
    chunks: list[BaseMessage | BaseMessageChunk] = []
    for chunk in llm_with_tools.stream(query):
        chunks = [*chunks, chunk]
        if first:
            gathered = chunk
            first = False
        else:
            gathered = gathered + chunk  # type: ignore[assignment]
        for block in chunk.content_blocks:
            assert block["type"] in ("text", "tool_call_chunk")
    assert len(chunks) > 1
    assert isinstance(gathered.content, list)
    assert len(gathered.content) == 2
    tool_use_block = None
    for content_block in gathered.content:
        assert isinstance(content_block, dict)
        if content_block["type"] == "tool_use":
            tool_use_block = content_block
            break
    assert tool_use_block is not None
    assert tool_use_block["name"] == "get_weather"
    assert "location" in json.loads(tool_use_block["partial_json"])
    assert isinstance(gathered, AIMessageChunk)
    assert isinstance(gathered.tool_calls, list)
    assert len(gathered.tool_calls) == 1
    tool_call = gathered.tool_calls[0]
    assert tool_call["name"] == "get_weather"
    assert isinstance(tool_call["args"], dict)
    assert "location" in tool_call["args"]
    assert tool_call["id"] is not None

    content_blocks = gathered.content_blocks
    assert len(content_blocks) == 2
    assert content_blocks[0]["type"] == "text"
    assert content_blocks[0]["text"]
    assert content_blocks[1]["type"] == "tool_call"
    assert content_blocks[1]["name"] == "get_weather"
    assert content_blocks[1]["args"]

    # Test passing response back to model
    stream = llm_with_tools.stream(
        [
            query,
            gathered,
            ToolMessage(content="sunny and warm", tool_call_id=tool_call["id"]),
        ],
    )
    chunks = []
    first = True
    for chunk in stream:
        chunks = [*chunks, chunk]
        if first:
            gathered = chunk
            first = False
        else:
            gathered = gathered + chunk  # type: ignore[assignment]
    assert len(chunks) > 1