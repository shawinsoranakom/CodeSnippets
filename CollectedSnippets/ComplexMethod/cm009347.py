def test_web_search_v1() -> None:
    llm = ChatGroq(model="groq/compound", output_version="v1")
    input_message = {
        "role": "user",
        "content": "Search for the weather in Boston today.",
    }
    full: AIMessageChunk | None = None
    for chunk in llm.stream([input_message]):
        full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert full.additional_kwargs["reasoning_content"]
    assert full.additional_kwargs["executed_tools"]
    assert [block["type"] for block in full.content_blocks] == [
        "reasoning",
        "server_tool_call",
        "server_tool_result",
        "reasoning",
        "text",
    ]

    next_message = {
        "role": "user",
        "content": "Now search for the weather in San Francisco.",
    }
    response = llm.invoke([input_message, full, next_message])
    assert [block["type"] for block in response.content_blocks] == [
        "reasoning",
        "server_tool_call",
        "server_tool_result",
        "text",
    ]