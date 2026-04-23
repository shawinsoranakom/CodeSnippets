def test_web_search(output_version: Literal["v0", "v1"]) -> None:
    llm = ChatAnthropic(
        model=MODEL_NAME,  # type: ignore[call-arg]
        max_tokens=1024,
        output_version=output_version,
    )

    tool = {"type": "web_search_20250305", "name": "web_search", "max_uses": 1}
    llm_with_tools = llm.bind_tools([tool])

    input_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "How do I update a web app to TypeScript 5.5?",
            },
        ],
    }
    response = llm_with_tools.invoke([input_message])
    assert all(isinstance(block, dict) for block in response.content)
    block_types = {block["type"] for block in response.content}  # type: ignore[index]
    if output_version == "v0":
        assert block_types == {"text", "server_tool_use", "web_search_tool_result"}
    else:
        assert block_types == {"text", "server_tool_call", "server_tool_result"}

    # Test streaming
    full: BaseMessageChunk | None = None
    for chunk in llm_with_tools.stream([input_message]):
        assert isinstance(chunk, AIMessageChunk)
        full = chunk if full is None else full + chunk

    assert isinstance(full, AIMessageChunk)
    assert isinstance(full.content, list)
    block_types = {block["type"] for block in full.content}  # type: ignore[index]
    if output_version == "v0":
        assert block_types == {"text", "server_tool_use", "web_search_tool_result"}
    else:
        assert block_types == {"text", "server_tool_call", "server_tool_result"}

    # Test we can pass back in
    next_message = {
        "role": "user",
        "content": "Please repeat the last search, but focus on sources from 2024.",
    }
    _ = llm_with_tools.invoke(
        [input_message, full, next_message],
    )